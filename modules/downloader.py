"""Module for downloader manager"""

from bases.abs import ModuleBase
from bases.enums import MediaType
from system.config import Config
from system.logger import log
from system.database import Database as db


class DownloaderModule(ModuleBase):
    """Downloader manager module"""

    def __init__(self, media_type: MediaType):
        self._name = "Downloader"
        self._type = media_type.value
        self._ready = self._is_required_config_set([
            'DOWNLOADER_URL',
            'DOWNLOADER_USER',
            'DOWNLOADER_PASSW',
        ])
        self._req = self._init(
            url=Config().downloader_url + "/api/v2"
        )
        if self._ready:
            self._sid = self._auth()
            self._torrents = [item.get('name') for item in self._list()]

    def export(self):
        """Export the module data"""
        for item in db().get_all(self._type):
            if (
                item.get('favorite') == 'true'
                and
                item.get('link')
                and
                item.get('collected') != 'false'
            ):
                if item.get('torrent') not in self._torrents:
                    if self._add(item.get('link')):
                        log(
                            f"Send '{item.get('title')} ({item.get('year')})' "
                            "to the downloader manager"
                        )
                    else:
                        log(
                            f"Failed to send '{item.get('title')} ({item.get('year')})' "
                            "to the downloader manager",
                            level='WARNING'
                        )
                else:
                    log(
                        f"'{item.get('title')} ({item.get('year')}' "
                        "already in the downloader",
                        level='DEBUG'
                    )

    def _auth(self) -> str:
        response = self._req.post(
            endpoint="auth/login",
            data={"username": Config().downloader_user, "password": Config().downloader_passw},
            key="sid"
        )
        sid = response.cookies.get("SID")
        if not sid:
            log("Failed to authenticate with the downloader", level="ERROR")
            self._ready = False
        return sid

    def _list(self) -> list:
        response = self._req.get(
            endpoint="torrents/info",
            cookies={"SID": self._sid},
        )
        return response.data

    def _add(self, link: str) -> bool:
        data = {"urls": link}
        if Config().downloader_savepath:
            data["savepath"] = Config().downloader_savepath
        response = self._req.post(
            endpoint="torrents/add",
            data=data,
            cookies={"SID": self._sid},
        )
        return response.status == 200
