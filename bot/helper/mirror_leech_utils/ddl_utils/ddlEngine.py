#!/usr/bin/env python3
import json
from pathlib import Path
from traceback import format_exc
from json import JSONDecodeError
from io import BufferedReader
from re import findall as re_findall
from aiofiles.os import path as aiopath
from time import time
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)
from aiohttp import ClientSession
from aiohttp.client_exceptions import ContentTypeError

from .... import LOGGER
from ....core.config_manager import Config
from bot.helper.mirror_leech_utils.ddl_utils.gofile import Gofile
from bot.helper.ext_utils.files_utils import get_mime_type


class ProgressFileReader(BufferedReader):
    def __init__(self, filename, read_callback=None):
        super().__init__(open(filename, "rb"))
        self.__read_callback = read_callback
        self.length = Path(filename).stat().st_size

    def read(self, size=None):
        size = size or (self.length - self.tell())
        if self.__read_callback:
            self.__read_callback(self.tell())
        return super().read(size)


class DDLUploader:
    def __init__(self, listener=None, name=None, path=None):
        self.name = name
        self.__processed_bytes = 0
        self.last_uploaded = 0
        self.__listener = listener
        self.__path = path
        self.__start_time = time()
        self.total_files = 0
        self.total_folders = 0
        self.is_cancelled = False
        self.__is_errored = False
        self.__ddl_servers = {}
        self.__engine = "DDL v1"
        self.__asyncSession = None
        self.__user_id = self.__listener.message.from_user.id

    async def __user_settings(self):
        ddl_servers_env = Config.DDL_SERVERS  # Already a dict
        self.__ddl_servers = {
            serv: (data["enabled"], data["key"]) for serv, data in ddl_servers_env.items()
        }

    def __progress_callback(self, current):
        chunk_size = current - self.last_uploaded
        self.last_uploaded = current
        self.__processed_bytes += chunk_size

    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=8),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
    )
    async def upload_aiohttp(self, url, file_path, req_file, data):
        with ProgressFileReader(
            filename=file_path, read_callback=self.__progress_callback
        ) as file:
            data[req_file] = file
            async with ClientSession() as self.__asyncSession:
                async with self.__asyncSession.post(url, data=data) as resp:
                    if resp.status == 200:
                        try:
                            return await resp.json()
                        except ContentTypeError:
                            return "Uploaded"
                        except JSONDecodeError:
                            return None

    async def __upload_to_ddl(self, file_path):
        all_links = {}
        for serv, (enabled, api_key) in self.__ddl_servers.items():
            if enabled:
                self.total_files = 0
                self.total_folders = 0
                if serv == "gofile":
                    self.__engine = "GoFile API"
                    nlink = await Gofile(self, api_key).upload(file_path)
                    all_links["GoFile"] = nlink
                self.__processed_bytes = 0
        if not all_links:
            raise Exception("No DDL Enabled to Upload.")
        return all_links

    async def upload(self, file_name, size):
        item_path = f"{self.__path}/{file_name}"
        LOGGER.info(f"Uploading: {item_path} via DDL")
        await self.__user_settings()
        try:
            if await aiopath.isfile(item_path):
                mime_type = get_mime_type(item_path)
            else:
                mime_type = "Folder"
            link = await self.__upload_to_ddl(item_path)
            if link is None:
                raise Exception("Upload has been manually cancelled!")
            if self.is_cancelled:
                return
            LOGGER.info(f"Uploaded To DDL: {item_path}")
        except Exception as err:
            LOGGER.info("DDL Upload has been Cancelled")
            if self.__asyncSession:
                await self.__asyncSession.close()
            err = str(err).replace(">", "").replace("<", "")
            LOGGER.info(format_exc())
            await self.__listener.on_upload_error(err)
            self.__is_errored = True
        finally:
            if self.is_cancelled or self.__is_errored:
                return
            await self.__listener.on_upload_complete(
                link, self.total_files, self.total_folders, mime_type
            )

    @property
    def speed(self):
        try:
            return self.__processed_bytes / int(time() - self.__start_time)
        except ZeroDivisionError:
            return 0

    @property
    def processed_bytes(self):
        return self.__processed_bytes

    @property
    def engine(self):
        return self.__engine

    async def cancel_task(self):
        self.is_cancelled = True
        LOGGER.info(f"Cancelling Upload: {self.name}")
        if self.__asyncSession:
            await self.__asyncSession.close()
        await self.__listener.on_download_error("Download Cancelled by User!")
