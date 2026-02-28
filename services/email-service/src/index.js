/**
 * CareerTrojan Email Microservice
 * 
 * Unified email handling for:
 * - Klaviyo (marketing campaigns, user engagement)
 * - SendGrid (transactional, backup)
 * - Zendesk (support tickets)
 * - Token-based email responses
 * - User-Mentor communication
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import { logger } from './utils/logger.js';
import { healthRouter } from './routes/health.js';
import { klaviyoRouter } from './routes/klaviyo.js';
import { sendgridRouter } from './routes/sendgrid.js';
import { zendeskRouter } from './routes/zendesk.js';
import { tokenRouter } from './routes/token-response.js';
import { mentorRouter } from './routes/mentor-emails.js';
import { webhookRouter } from './routes/webhooks.js';

dotenv.config();

const app = express();
const PORT = process.env.EMAIL_SERVICE_PORT || 3050;

// Middleware
app.use(helmet());
app.use(cors({
    origin: process.env.CORS_ORIGINS?.split(',') || ['http://localhost:8600', 'http://localhost:8601'],
    credentials: true
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Request logging
app.use((req, res, next) => {
    logger.info(`${req.method} ${req.path}`, { 
        ip: req.ip, 
        userAgent: req.get('User-Agent')?.substring(0, 50) 
    });
    next();
});

// Routes
app.use('/health', healthRouter);
app.use('/api/email/klaviyo', klaviyoRouter);
app.use('/api/email/sendgrid', sendgridRouter);
app.use('/api/email/zendesk', zendeskRouter);
app.use('/api/email/token', tokenRouter);
app.use('/api/email/mentor', mentorRouter);
app.use('/api/webhooks', webhookRouter);

// Root endpoint
app.get('/', (req, res) => {
    res.json({
        service: 'CareerTrojan Email Service',
        version: '1.0.0',
        providers: ['klaviyo', 'sendgrid', 'zendesk'],
        features: ['token-response', 'mentor-emails', 'webhooks'],
        status: 'operational'
    });
});

// Error handler
app.use((err, req, res, next) => {
    logger.error('Unhandled error', { error: err.message, stack: err.stack });
    res.status(500).json({ 
        error: 'Internal server error',
        requestId: req.headers['x-request-id'] || 'unknown'
    });
});

// Start server
app.listen(PORT, () => {
    logger.info(`Email service running on port ${PORT}`);
    logger.info('Providers:', {
        klaviyo: !!process.env.KLAVIYO_API_KEY,
        sendgrid: !!process.env.SENDGRID_API_KEY,
        zendesk: !!process.env.ZENDESK_API_TOKEN
    });
});

export default app;
