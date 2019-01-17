# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import random
from threading import Lock

from fake_useragent import settings
from fake_useragent.errors import FakeUserAgentError
from fake_useragent.log import logger
from fake_useragent.utils import load, load_cached, str_types, update

#check is ua mobile
import re
import time
import configparser
import os

reg_b = re.compile(r"(android|bb\\d+|meego).+mobile|avantgo|bada\\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\\.(browser|link)|vodafone|wap|windows ce|xda|xiino", re.I|re.M)
reg_v = re.compile(r"1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\\-(n|u)|c55\\/|capi|ccwa|cdm\\-|cell|chtm|cldc|cmd\\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\\-s|devi|dica|dmob|do(c|p)o|ds(12|\\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\\-|_)|g1 u|g560|gene|gf\\-5|g\\-mo|go(\\.w|od)|gr(ad|un)|haie|hcit|hd\\-(m|p|t)|hei\\-|hi(pt|ta)|hp( i|ip)|hs\\-c|ht(c(\\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\\-(20|go|ma)|i230|iac( |\\-|\\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\\/)|klon|kpt |kwc\\-|kyo(c|k)|le(no|xi)|lg( g|\\/(k|l|u)|50|54|\\-[a-w])|libw|lynx|m1\\-w|m3ga|m50\\/|ma(te|ui|xo)|mc(01|21|ca)|m\\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\\-2|po(ck|rt|se)|prox|psio|pt\\-g|qa\\-a|qc(07|12|21|32|60|\\-[2-7]|i\\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\\-|oo|p\\-)|sdk\\/|se(c(\\-|0|1)|47|mc|nd|ri)|sgh\\-|shar|sie(\\-|m)|sk\\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\\-|v\\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\\-|tdg\\-|tel(i|m)|tim\\-|t\\-mo|to(pl|sh)|ts(70|m\\-|m3|m5)|tx\\-9|up(\\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\\-|your|zeto|zte\\-", re.I|re.M)

#config settings for mobile ua controlling
config = configparser.ConfigParser()
file_basepath = os.path.dirname(os.path.abspath(__file__))
config.read_file(file_basepath+'/mobile_ua.cfg')
MOBILE_UA = config.get('SETTINGS', 'MOBILE_UA')
DISPLAY_MOBILE_UA_CHECK_TIME = config.get('SETTINGS', 'DISPLAY_MOBILE_UA_CHECK_TIME')

class FakeUserAgent(object):
    def __init__(
        self,
        cache=True,
        use_cache_server=True,
        path=settings.DB,
        fallback=None,
        verify_ssl=True,
        safe_attrs=tuple(),
    ):
        assert isinstance(cache, bool), \
            'cache must be True or False'

        self.cache = cache

        assert isinstance(use_cache_server, bool), \
            'use_cache_server must be True or False'

        self.use_cache_server = use_cache_server

        assert isinstance(path, str_types), \
            'path must be string or unicode'

        self.path = path

        if fallback is not None:
            assert isinstance(fallback, str_types), \
                'fallback must be string or unicode'

        self.fallback = fallback

        assert isinstance(verify_ssl, bool), \
            'verify_ssl must be True or False'

        self.verify_ssl = verify_ssl

        assert isinstance(safe_attrs, (list, set, tuple)), \
            'safe_attrs must be list\\tuple\\set of strings or unicode'

        if safe_attrs:
            str_types_safe_attrs = [
                isinstance(attr, str_types) for attr in safe_attrs
            ]

            assert all(str_types_safe_attrs), \
                'safe_attrs must be list\\tuple\\set of strings or unicode'

        self.safe_attrs = set(safe_attrs)

        # initial empty data
        self.data = {}
        # TODO: change source file format
        # version 0.1.4+ migration tool
        self.data_randomize = []
        self.data_browsers = {}

        self.load()

    def load(self):
        try:
            with self.load.lock:
                if self.cache:
                    self.data = load_cached(
                        self.path,
                        use_cache_server=self.use_cache_server,
                        verify_ssl=self.verify_ssl,
                    )
                else:
                    self.data = load(
                        use_cache_server=self.use_cache_server,
                        verify_ssl=self.verify_ssl,
                    )

                # TODO: change source file format
                # version 0.1.4+ migration tool
                self.data_randomize = list(self.data['randomize'].values())
                self.data_browsers = self.data['browsers']
        except FakeUserAgentError:
            if self.fallback is None:
                raise
            else:
                logger.warning(
                    'Error occurred during fetching data, '
                    'but was suppressed with fallback.',
                )
    load.lock = Lock()

    def update(self, cache=None):
        with self.update.lock:
            if cache is not None:
                assert isinstance(cache, bool), \
                    'cache must be True or False'

                self.cache = cache

            if self.cache:
                update(
                    self.path,
                    use_cache_server=self.use_cache_server,
                    verify_ssl=self.verify_ssl,
                )

            self.load()
    update.lock = Lock()

    def __getitem__(self, attr):
        return self.__getattr__(attr)

    def __getattr__(self, attr):
        if attr in self.safe_attrs:
            return super(UserAgent, self).__getattr__(attr)

        try:
            for value, replacement in settings.REPLACEMENTS.items():
                attr = attr.replace(value, replacement)

            attr = attr.lower()

            if attr == 'random':
                browser = random.choice(self.data_randomize)
            else:
                browser = settings.SHORTCUTS.get(attr, attr)

            #rotate random ua while we will obtaine not mobile ua
            created_ua = random.choice(self.data_browsers[browser])
            mobile_ua = MOBILE_UA.lower()
            #ua only non-mobile
            while mobile_ua is 'no' and self.is_ua_mobile(created_ua):
                created_ua = random.choice(self.data_browsers[browser])
            #ua only mobile
            while mobile_ua is 'yes' and not self.is_ua_mobile(created_ua):
                created_ua = random.choice(self.data_browsers[browser])
            return created_ua

        except (KeyError, IndexError):
            if self.fallback is None:
                raise FakeUserAgentError('Error occurred during getting browser')  # noqa
            else:
                logger.warning(
                    'Error occurred during getting browser, '
                    'but was suppressed with fallback.',
                )

                return self.fallback

    def is_ua_mobile(self, user_agent):
        if DISPLAY_MOBILE_UA_CHECK_TIME:
            time_start = time.time()
        b = reg_b.search(user_agent)
        v = reg_v.search(user_agent[0:4])
        if settings.DISPLAY_MOBILE_UA_CHECK_TIME:
            print("Time wasted for mobile user-agent checking={}s".format(round(time.time()-time_start, 3)))
        if b or v:
            return True
        else:
            return False


# common alias
UserAgent = FakeUserAgent
