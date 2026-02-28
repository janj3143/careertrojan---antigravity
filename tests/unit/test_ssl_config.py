"""
SSL/TLS and nginx configuration tests.
Validates production-readiness of TLS configs, security headers,
HSTS, certificate paths, and k8s ingress setup.
"""
import pathlib, re, pytest, yaml, json

CONFIG_DIR = pathlib.Path(r"C:\careertrojan\config")


class TestNginxTLS:
    """Nginx portal-bridge.conf TLS validation."""

    CONF_FILE = CONFIG_DIR / "nginx" / "portal-bridge.conf"

    def test_conf_exists(self):
        assert self.CONF_FILE.exists()

    def test_tls_12_and_13_enabled(self):
        content = self.CONF_FILE.read_text("utf-8")
        assert "TLSv1.2" in content, "TLS 1.2 not enabled"
        assert "TLSv1.3" in content, "TLS 1.3 not enabled"

    def test_no_weak_protocols(self):
        content = self.CONF_FILE.read_text("utf-8")
        assert "SSLv2" not in content, "SSLv2 must not be enabled"
        assert "SSLv3" not in content, "SSLv3 must not be enabled"
        assert "TLSv1.0" not in content or "TLSv1.0" not in \
            re.findall(r"ssl_protocols\s+([^;]+)", content)[0] if \
            re.findall(r"ssl_protocols\s+([^;]+)", content) else True

    def test_ssl_cert_paths_defined(self):
        content = self.CONF_FILE.read_text("utf-8")
        assert "ssl_certificate" in content
        assert "ssl_certificate_key" in content
        assert "/etc/ssl/certs/careertrojan.crt" in content
        assert "/etc/ssl/private/careertrojan.key" in content

    def test_http_to_https_redirect(self):
        content = self.CONF_FILE.read_text("utf-8")
        assert "return 301 https://" in content, "Missing HTTP→HTTPS redirect"

    def test_security_headers_present(self):
        content = self.CONF_FILE.read_text("utf-8")
        assert "X-Frame-Options" in content
        assert "X-Content-Type-Options" in content
        assert "nosniff" in content

    def test_strong_ciphers(self):
        content = self.CONF_FILE.read_text("utf-8")
        assert "HIGH:!aNULL:!MD5" in content or "ECDHE" in content

    def test_http2_enabled(self):
        content = self.CONF_FILE.read_text("utf-8")
        assert "http2" in content, "HTTP/2 not enabled"

    def test_all_location_blocks_present(self):
        content = self.CONF_FILE.read_text("utf-8")
        for loc in ["/admin", "/mentor", "/api", "/"]:
            assert f"location {loc}" in content, f"Missing location block: {loc}"


class TestK8sIngress:
    """Kubernetes ingress TLS and cert-manager validation."""

    K8S_FILE = CONFIG_DIR / "k8s" / "deployment.yaml"

    def test_deployment_yaml_exists(self):
        assert self.K8S_FILE.exists()

    def test_cert_manager_annotation(self):
        content = self.K8S_FILE.read_text("utf-8")
        assert "cert-manager.io/cluster-issuer" in content
        assert "letsencrypt-prod" in content

    def test_tls_secret_defined(self):
        content = self.K8S_FILE.read_text("utf-8")
        assert "careertrojan-tls" in content

    def test_host_is_careertrojan_com(self):
        content = self.K8S_FILE.read_text("utf-8")
        assert "careertrojan.com" in content

    def test_ingress_paths_complete(self):
        content = self.K8S_FILE.read_text("utf-8")
        for path in ["/api", "/admin", "/mentor", "/"]:
            assert f"path: {path}" in content, f"Ingress missing path: {path}"


class TestSendGridDNS:
    """SendGrid DNS CNAME records validation."""

    DNS_FILE = CONFIG_DIR / "dns" / "sendgrid_cname.yaml"

    def test_dns_file_exists(self):
        assert self.DNS_FILE.exists()

    def test_has_all_required_records(self):
        content = self.DNS_FILE.read_text("utf-8")
        assert "em227.careertrojan.com" in content, "Missing email branding CNAME"
        assert "s1._domainkey" in content, "Missing DKIM key 1"
        assert "s2._domainkey" in content, "Missing DKIM key 2"
        assert "_dmarc" in content, "Missing DMARC record"

    def test_dmarc_policy_is_quarantine_or_reject(self):
        content = self.DNS_FILE.read_text("utf-8")
        assert "p=quarantine" in content or "p=reject" in content, \
            "DMARC policy should be quarantine or reject for production"

    def test_sendgrid_env_vars_defined(self):
        content = self.DNS_FILE.read_text("utf-8")
        assert "SENDGRID_API_KEY" in content
        assert "SENDGRID_FROM_EMAIL" in content
        assert "noreply@careertrojan.com" in content


class TestDockerSSL:
    """Docker compose SSL volume configuration."""

    COMPOSE_LOCKSTEP = CONFIG_DIR / "docker" / "docker-compose.lockstep.yml"

    def test_lockstep_compose_exists(self):
        assert self.COMPOSE_LOCKSTEP.exists()

    def test_ssl_volume_mounted(self):
        content = self.COMPOSE_LOCKSTEP.read_text("utf-8")
        assert "ssl" in content.lower(), "SSL volume not mounted"

    def test_ports_443_exposed(self):
        content = self.COMPOSE_LOCKSTEP.read_text("utf-8")
        assert "443" in content, "Port 443 not exposed"
