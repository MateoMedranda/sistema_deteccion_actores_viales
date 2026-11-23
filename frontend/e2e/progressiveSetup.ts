import { execFileSync } from "node:child_process";
import path from "node:path";
export default function setup() {
  const python = process.env.PROGRESSIVE_TEST_PYTHON;
  if (!python)
    throw Error("No se encontró Python 3.12 con las dependencias de prueba.");
  execFileSync(
    python,
    [path.resolve("../backend/scripts/prepare_progressive_fixtures.py")],
    { cwd: path.resolve(".."), stdio: "pipe" },
  );
}
