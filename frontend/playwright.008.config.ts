import { backendPython } from "./playwright.backend";
import base from "./playwright.config";
import {defineConfig} from "@playwright/test";
export default defineConfig({...base,testIgnore:[],testMatch:/(workspace-navigation|managed-session|video-presentation|video-analysis-flow|scene-viewport|video-track-details)\.spec\.ts/,webServer:[
 {command:`${backendPython} -m uvicorn tests.e2e.serve_managed_gateway:app --host 127.0.0.1 --port 4174`,cwd:"../backend",url:"http://127.0.0.1:4174/health/live",reuseExistingServer:false,timeout:30000},
 {command:`${backendPython} -m uvicorn tests.e2e.serve_managed_test_api:app --host 127.0.0.1 --port 8767`,cwd:"../backend",url:"http://127.0.0.1:8767/health/live",reuseExistingServer:false,timeout:60000},
 {command:"npm run dev -- --host 127.0.0.1 --port 4173 --strictPort",url:"http://127.0.0.1:4173",reuseExistingServer:false,timeout:30000}
]});
