import unittest

from aiohttp import web
from multidict import CIMultiDict

from weread_exporter import utils


class FetchHeadersTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        async def handler(_request):
            headers = CIMultiDict()
            headers.add("Set-Cookie", "session=first")
            headers.add("Set-Cookie", "token=second")
            return web.Response(body=b"ok", headers=headers)

        app = web.Application()
        app.router.add_get("/", handler)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "127.0.0.1", 0)
        await self.site.start()
        port = self.site._server.sockets[0].getsockname()[1]
        self.url = "http://127.0.0.1:%d/" % port

    async def asyncTearDown(self):
        await self.runner.cleanup()

    async def test_response_headers_preserve_duplicate_set_cookie_values(self):
        status, headers, body = await utils.fetch(
            self.url, respond_with_headers=True
        )

        self.assertEqual(status, 200)
        self.assertEqual(body, b"ok")
        self.assertEqual(
            headers.getall("Set-Cookie"),
            ["session=first", "token=second"],
        )


if __name__ == "__main__":
    unittest.main()
