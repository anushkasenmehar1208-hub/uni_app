import asyncio
import unittest

from starlette.requests import Request

from uni_app import uni_app as app_module


def make_request(
    path: str,
    host: str,
    *,
    scheme: str = "http",
    path_params: dict[str, str] | None = None,
) -> Request:
    server_host, _, port_text = host.partition(":")
    port = int(port_text) if port_text else (443 if scheme == "https" else 80)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": scheme,
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [(b"host", host.encode("utf-8"))],
        "client": ("127.0.0.1", 54321),
        "server": (server_host, port),
        "path_params": path_params or {},
    }
    return Request(scope)


class RoutingTests(unittest.TestCase):
    def test_scope_routes_stay_static(self) -> None:
        self.assertEqual(app_module.scope_to_route("home"), "/s/home")
        self.assertEqual(app_module.scope_to_route("y1s1"), "/s/y1s1")

    def test_frontend_base_url_uses_same_single_port_origin_locally(self) -> None:
        request = make_request("/auth/google/callback", "127.0.0.1:8124")
        self.assertEqual(app_module._frontend_base_url(request), "http://127.0.0.1:8124")

    def test_frontend_base_url_keeps_configured_frontend_for_split_local_dev(self) -> None:
        request = make_request("/auth/google/callback", "localhost:8000")
        self.assertEqual(app_module._frontend_base_url(request), "http://localhost:3000")

    def test_google_callback_url_uses_same_single_port_origin_locally(self) -> None:
        request = make_request("/auth/google/start", "127.0.0.1:8124")
        self.assertEqual(
            app_module._google_callback_url(request),
            "http://127.0.0.1:8124/auth/google/callback",
        )

    def test_google_callback_url_keeps_configured_frontend_for_split_local_dev(self) -> None:
        request = make_request("/auth/google/start", "localhost:8000")
        self.assertEqual(
            app_module._google_callback_url(request),
            "http://localhost:3000/auth/google/callback",
        )

    def test_legacy_auth_complete_redirect_targets_static_page(self) -> None:
        request = make_request(
            "/auth/complete/abc123",
            "127.0.0.1:8124",
            path_params={"token": "abc123"},
        )
        response = asyncio.run(app_module.legacy_auth_complete_redirect(request))
        self.assertEqual(
            response.headers["location"],
            "http://127.0.0.1:8124/auth/complete?token=abc123",
        )

    def test_legacy_google_complete_redirect_targets_static_page(self) -> None:
        request = make_request(
            "/auth/google/complete/code/state/origin",
            "127.0.0.1:8124",
            path_params={"code": "code", "state": "state", "origin_b64": "origin"},
        )
        response = asyncio.run(app_module.legacy_google_complete_redirect(request))
        self.assertEqual(
            response.headers["location"],
            "http://127.0.0.1:8124/auth/google/complete?code=code&state=state&origin_b64=origin",
        )


if __name__ == "__main__":
    unittest.main()
