import axios, { AxiosResponse, AxiosRequestConfig, RawAxiosRequestHeaders, InternalAxiosRequestConfig, Axios, AxiosInstance, AxiosError } from 'axios';
import express, { Request, Response } from "express";
import * as http from "http";
import { prependListener } from 'process';
import PrefectClient from './clients/prefect.js';
import expressCache from "cache-express";


const port = parseInt(process.env.PORT || '4003');
const app = express();

app.use(express.json());
app.use(express.urlencoded());

const server = http.createServer(app);

(async () => {
    console.log(process.env)
    let client = new PrefectClient(process.env.PREFECT_ACCOUNT_ID, process.env.PREFECT_WORKSPACE_ID);
    app.get('/status', expressCache({
		timeout: 1200000,
		onTimeout: (key, value) => {
			console.log(`Cache removed for key: ${key}`);
		},
	}), async (req, res) => {
        let latest = await client.getLatestFlowRunPerDeployment();
        res.json(latest)
    })

    app.get('/heartbeat', async (_req, res) => {
        res.send(200)
    })

    server.listen(port, () => {
        console.log(`Server is listening on port ${port}`);
    });
})();



