import express, { type Express } from "express";
import cors from "cors";
import pinoHttp from "pino-http";
import router from "./routes";
import { logger } from "./lib/logger";

const app: Express = express();

app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return {
          id: req.id,
          method: req.method,
          url: req.url?.split("?")[0],
        };
      },
      res(res) {
        return {
          statusCode: res.statusCode,
        };
      },
    },
  }),
);
// In production, restrict cross-origin access to *.replit.app only.
// The /api/healthz endpoint exposes no sensitive data, but an open wildcard
// allows any site to make credentialed cross-origin reads — unnecessarily broad.
const corsOrigin =
  process.env["NODE_ENV"] === "production"
    ? (origin: string | undefined, cb: (e: Error | null, allow?: boolean) => void) => {
        if (!origin || /^https:\/\/[^.]+\.replit\.app$/.test(origin)) {
          cb(null, true);
        } else {
          cb(new Error("CORS: origin not allowed"));
        }
      }
    : true;

app.use(cors({ origin: corsOrigin }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use("/api", router);

export default app;
