/**
 * Health Check Routes
 */

import { Router } from 'express';
import { checkKlaviyoConnection } from '../providers/klaviyo.js';
import { checkSendgridConnection } from '../providers/sendgrid.js';
import { checkZendeskConnection } from '../providers/zendesk.js';

export const healthRouter = Router();

healthRouter.get('/', async (req, res) => {
    const health = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        providers: {}
    };

    try {
        health.providers.klaviyo = await checkKlaviyoConnection();
        health.providers.sendgrid = await checkSendgridConnection();
        health.providers.zendesk = await checkZendeskConnection();
        
        // Overall status based on at least one email provider working
        const hasEmailProvider = health.providers.klaviyo.connected || 
                                 health.providers.sendgrid.connected;
        health.status = hasEmailProvider ? 'healthy' : 'degraded';
    } catch (error) {
        health.status = 'unhealthy';
        health.error = error.message;
    }

    const statusCode = health.status === 'healthy' ? 200 : 
                       health.status === 'degraded' ? 200 : 503;
    res.status(statusCode).json(health);
});

healthRouter.get('/ready', (req, res) => {
    res.json({ ready: true, timestamp: new Date().toISOString() });
});

healthRouter.get('/live', (req, res) => {
    res.json({ alive: true, pid: process.pid });
});
