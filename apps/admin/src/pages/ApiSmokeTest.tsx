import { useEffect, useState } from "react";
import { apiGet } from "../lib/apiClient";

export default function ApiSmokeTest() {
  const [out, setOut] = useState<any>(null);

  useEffect(() => {
    apiGet("/health").then(setOut);
  }, []);

  return (
    <div style={{ padding: 16 }}>
      <h2>API Smoke Test</h2>
      <pre>{JSON.stringify(out, null, 2)}</pre>
    </div>
  );
}
