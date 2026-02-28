"""
Frontend route integrity tests.
Validates all frontend routes have matching page components,
no broken links, and consistent navigation.
"""
import pathlib, re, pytest

APPS_DIR = pathlib.Path(r"C:\careertrojan\apps")


def extract_routes_from_tsx(filepath: pathlib.Path) -> list[dict]:
    """Extract Route path definitions from App.tsx."""
    content = filepath.read_text("utf-8")
    routes = []
    for m in re.finditer(r'path=["\']([^"\']+)["\']', content):
        routes.append({"path": m.group(1), "file": str(filepath)})
    return routes


def extract_links_from_tsx(filepath: pathlib.Path) -> list[dict]:
    """Extract Link to= and a href= targets from a TSX file."""
    content = filepath.read_text("utf-8")
    links = []
    # React Router Links
    for m in re.finditer(r'(?:to|href)=["\'](/[^"\']*)["\']', content):
        target = m.group(1)
        if not target.startswith("/api") and target != "#":
            links.append({"target": target, "file": str(filepath)})
    return links


class TestUserAppRoutes:
    """User portal route integrity."""

    APP_TSX = APPS_DIR / "user" / "src" / "App.tsx"
    PAGES_DIR = APPS_DIR / "user" / "src" / "pages"

    def test_app_tsx_exists(self):
        assert self.APP_TSX.exists()

    def test_all_routes_defined(self):
        routes = extract_routes_from_tsx(self.APP_TSX)
        assert len(routes) >= 15, f"Only {len(routes)} routes, expected >= 15"

    def test_no_broken_page_imports(self):
        content = self.APP_TSX.read_text("utf-8")
        imports = re.findall(r"from\s+['\"]\.\/pages\/(\w+)['\"]", content)
        for page in imports:
            page_file = self.PAGES_DIR / f"{page}.tsx"
            assert page_file.exists(), f"Imported page missing: {page}.tsx"

    def test_dashboard_links_valid(self):
        dashboard = self.PAGES_DIR / "Dashboard.tsx"
        if not dashboard.exists():
            pytest.skip("Dashboard.tsx not found")
        links = extract_links_from_tsx(dashboard)
        routes = extract_routes_from_tsx(self.APP_TSX)
        route_paths = {r["path"] for r in routes}
        for link in links:
            # Allow /mentor/apply (cross-app)
            if link["target"].startswith("/mentor"):
                continue
            assert link["target"] in route_paths, \
                f"Dashboard link {link['target']} not in user routes"


class TestAdminAppRoutes:
    """Admin portal route integrity."""

    APP_TSX = APPS_DIR / "admin" / "src" / "App.tsx"
    PAGES_DIR = APPS_DIR / "admin" / "src" / "pages"

    def test_app_tsx_exists(self):
        assert self.APP_TSX.exists()

    def test_all_routes_defined(self):
        routes = extract_routes_from_tsx(self.APP_TSX)
        assert len(routes) >= 50, f"Only {len(routes)} admin routes, expected >= 50"

    def test_no_broken_page_imports(self):
        content = self.APP_TSX.read_text("utf-8")
        imports = re.findall(r"from\s+['\"]\.\/pages\/(\w+)['\"]", content)
        for page in imports:
            page_file = self.PAGES_DIR / f"{page}.tsx"
            assert page_file.exists(), f"Admin imported page missing: {page}.tsx"

    def test_admin_home_links_valid(self):
        home = self.PAGES_DIR / "AdminHome.tsx"
        if not home.exists():
            pytest.skip("AdminHome.tsx not found")
        links = extract_links_from_tsx(home)
        routes = extract_routes_from_tsx(self.APP_TSX)
        route_paths = {r["path"] for r in routes}
        for link in links:
            assert link["target"] in route_paths, \
                f"AdminHome link {link['target']} not in admin routes"

    def test_intelligence_hub_links_valid(self):
        hub = self.PAGES_DIR / "IntelligenceHub.tsx"
        if not hub.exists():
            pytest.skip("IntelligenceHub.tsx not found")
        links = extract_links_from_tsx(hub)
        routes = extract_routes_from_tsx(self.APP_TSX)
        route_paths = {r["path"] for r in routes}
        for link in links:
            assert link["target"] in route_paths, \
                f"IntelligenceHub link {link['target']} not in admin routes"


class TestMentorAppRoutes:
    """Mentor portal route integrity."""

    APP_TSX = APPS_DIR / "mentor" / "src" / "App.tsx"
    PAGES_DIR = APPS_DIR / "mentor" / "src" / "pages"

    def test_app_tsx_exists(self):
        assert self.APP_TSX.exists()

    def test_all_routes_defined(self):
        routes = extract_routes_from_tsx(self.APP_TSX)
        assert len(routes) >= 10, f"Only {len(routes)} mentor routes, expected >= 10"

    def test_mentor_login_links_valid(self):
        login = self.PAGES_DIR / "MentorLogin.tsx"
        if not login.exists():
            pytest.skip("MentorLogin.tsx not found")
        links = extract_links_from_tsx(login)
        for link in links:
            # /mentor/apply is the user app route — cross-app is valid
            assert link["target"].startswith("/mentor"), \
                f"MentorLogin has unexpected link: {link['target']}"
