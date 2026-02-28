/**
 * Token-Based Email Response System
 * 
 * Allows users to respond to emails via unique tokens embedded in links.
 * Use cases:
 * - Quick feedback (👍/👎)
 * - One-click confirmations
 * - Survey responses
 * - Unsubscribe handling
 */

import { Router } from 'express';
import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';
import { logger } from '../utils/logger.js';
import { trackEvent } from '../providers/klaviyo.js';
import { sendEmail } from '../providers/sendgrid.js';

export const tokenRouter = Router();

const TOKEN_SECRET = process.env.EMAIL_TOKEN_SECRET || 'careertrojan-email-token-secret-change-me';
const TOKEN_EXPIRY = process.env.EMAIL_TOKEN_EXPIRY || '7d';
const BASE_URL = process.env.EMAIL_SERVICE_BASE_URL || 'http://localhost:3050';

// In-memory store for responses (replace with Redis/DB in production)
const responseStore = new Map();

/**
 * Generate a secure response token
 */
function generateToken(payload) {
    return jwt.sign({
        ...payload,
        jti: uuidv4(),
        iat: Date.now()
    }, TOKEN_SECRET, { expiresIn: TOKEN_EXPIRY });
}

/**
 * Verify and decode a response token
 */
function verifyToken(token) {
    try {
        return jwt.verify(token, TOKEN_SECRET);
    } catch (error) {
        logger.warn('Invalid token', { error: error.message });
        return null;
    }
}

/**
 * Create response links for an email
 * POST /api/email/token/create
 */
tokenRouter.post('/create', async (req, res) => {
    try {
        const { 
            recipientEmail, 
            recipientId,
            responseType = 'feedback',  // feedback, confirm, survey, unsubscribe
            options = [],               // e.g., ['yes', 'no'] or ['👍', '👎', '😐']
            metadata = {},
            expiresIn = '7d'
        } = req.body;

        if (!recipientEmail) {
            return res.status(400).json({ error: 'recipientEmail required' });
        }

        const links = {};
        const basePayload = {
            email: recipientEmail,
            userId: recipientId,
            type: responseType,
            metadata
        };

        // Generate a link for each option
        for (const option of options) {
            const token = generateToken({ ...basePayload, response: option });
            links[option] = `${BASE_URL}/api/email/token/respond/${token}`;
        }

        // Store the request for tracking
        const requestId = uuidv4();
        responseStore.set(requestId, {
            email: recipientEmail,
            type: responseType,
            options,
            createdAt: new Date().toISOString(),
            responded: false
        });

        logger.info('Response tokens created', { recipientEmail, responseType, options });

        res.json({
            success: true,
            requestId,
            links,
            expiresIn
        });
    } catch (error) {
        logger.error('Token creation failed', { error: error.message });
        res.status(500).json({ error: error.message });
    }
});

/**
 * Handle a token response (clicked link)
 * GET /api/email/token/respond/:token
 */
tokenRouter.get('/respond/:token', async (req, res) => {
    try {
        const { token } = req.params;
        const payload = verifyToken(token);

        if (!payload) {
            return res.status(400).send(`
                <!DOCTYPE html>
                <html>
                <head><title>Link Expired</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1>⏰ Link Expired</h1>
                    <p>This response link has expired or is invalid.</p>
                    <p>Please contact support if you need assistance.</p>
                </body>
                </html>
            `);
        }

        const { email, userId, type, response, metadata } = payload;

        // Track the response
        try {
            await trackEvent(email, `Email_Response_${type}`, {
                response,
                userId,
                ...metadata,
                respondedAt: new Date().toISOString()
            });
        } catch (e) {
            logger.warn('Klaviyo tracking failed', { error: e.message });
        }

        // Store the response
        logger.info('Email response received', { email, type, response });

        // Custom handling based on response type
        let redirectUrl = metadata.redirectUrl;
        let message = 'Thank you for your response!';

        switch (type) {
            case 'unsubscribe':
                message = 'You have been unsubscribed.';
                // TODO: Update subscription status in database
                break;
            case 'confirm':
                message = 'Your action has been confirmed.';
                break;
            case 'feedback':
                message = `Thanks for your feedback: ${response}`;
                break;
            case 'survey':
                message = 'Thank you for completing the survey!';
                break;
        }

        // Return a nice HTML response or redirect
        if (redirectUrl) {
            return res.redirect(redirectUrl);
        }

        res.send(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Response Received - CareerTrojan</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
                    .card { background: white; border-radius: 10px; padding: 40px; max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #0D9488; }
                    .response-badge { background: #0D9488; color: white; padding: 10px 20px; border-radius: 20px; display: inline-block; margin: 20px 0; font-size: 18px; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>✅ Response Received</h1>
                    <div class="response-badge">${response}</div>
                    <p>${message}</p>
                    <p style="color: #666; font-size: 14px;">You can close this window.</p>
                </div>
            </body>
            </html>
        `);
    } catch (error) {
        logger.error('Token response failed', { error: error.message });
        res.status(500).send('An error occurred processing your response.');
    }
});

/**
 * Create a one-click unsubscribe link
 * POST /api/email/token/unsubscribe-link
 */
tokenRouter.post('/unsubscribe-link', async (req, res) => {
    try {
        const { email, listId, campaignId } = req.body;
        
        if (!email) {
            return res.status(400).json({ error: 'email required' });
        }

        const token = generateToken({
            email,
            type: 'unsubscribe',
            response: 'unsubscribed',
            metadata: { listId, campaignId }
        });

        const unsubscribeUrl = `${BASE_URL}/api/email/token/respond/${token}`;
        
        // List-Unsubscribe header format for email clients
        const listUnsubscribeHeader = `<${unsubscribeUrl}>, <mailto:unsubscribe@careertrojan.com?subject=Unsubscribe%20${email}>`;

        res.json({
            success: true,
            unsubscribeUrl,
            listUnsubscribeHeader
        });
    } catch (error) {
        logger.error('Unsubscribe link creation failed', { error: error.message });
        res.status(500).json({ error: error.message });
    }
});

/**
 * Send an email with embedded response tokens
 * POST /api/email/token/send-with-responses
 */
tokenRouter.post('/send-with-responses', async (req, res) => {
    try {
        const {
            to,
            subject,
            bodyHtml,
            bodyText,
            responseOptions = ['👍 Yes', '👎 No'],
            responseType = 'feedback',
            metadata = {}
        } = req.body;

        if (!to || !subject) {
            return res.status(400).json({ error: 'to and subject required' });
        }

        // Generate response links
        const links = {};
        for (const option of responseOptions) {
            const token = generateToken({
                email: to,
                type: responseType,
                response: option,
                metadata
            });
            links[option] = `${BASE_URL}/api/email/token/respond/${token}`;
        }

        // Build response buttons HTML
        const buttonsHtml = responseOptions.map(option => `
            <a href="${links[option]}" style="display: inline-block; padding: 12px 24px; margin: 5px; background: #0D9488; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                ${option}
            </a>
        `).join('');

        const fullHtml = `
            ${bodyHtml || `<p>${bodyText || ''}</p>`}
            <div style="margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 10px; text-align: center;">
                <p style="margin-bottom: 15px; color: #666;">Please let us know:</p>
                ${buttonsHtml}
            </div>
        `;

        // Send via SendGrid
        const result = await sendEmail({
            to,
            subject,
            html: fullHtml,
            text: bodyText || subject
        });

        res.json({
            success: true,
            ...result,
            responseLinks: links
        });
    } catch (error) {
        logger.error('Send with responses failed', { error: error.message });
        res.status(500).json({ error: error.message });
    }
});
