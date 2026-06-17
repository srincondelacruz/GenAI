/**
 * Entry point — carga variables de entorno y lanza el host MCP.
 */

import "dotenv/config";
import { main } from "./host.js";

main().catch((err) => {
  console.error("Error fatal:", err);
  process.exit(1);
});
