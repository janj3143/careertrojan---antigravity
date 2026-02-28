/**
 * Request Validation Middleware
 */

import { logger } from '../utils/logger.js';

/**
 * Create validation middleware for a Joi schema
 */
export function validateRequest(schema) {
    return (req, res, next) => {
        const { error, value } = schema.validate(req.body, {
            abortEarly: false,
            stripUnknown: true
        });

        if (error) {
            const errors = error.details.map(d => ({
                field: d.path.join('.'),
                message: d.message
            }));
            
            logger.warn('Validation failed', { path: req.path, errors });
            
            return res.status(400).json({
                error: 'Validation failed',
                details: errors
            });
        }

        req.body = value;
        next();
    };
}

/**
 * API Key authentication middleware
 * Uses configurable header name (default: X-CareerTrojan-Token)
 */
export function requireApiKey(req, res, next) {
    const headerName = (process.env.EMAIL_SERVICE_AUTH_HEADER || 'X-CareerTrojan-Token').toLowerCase();
    const apiKey = req.headers[headerName] || req.headers['x-api-key'] || req.query.api_key;
    const validKey = process.env.EMAIL_SERVICE_API_KEY;

    if (!validKey) {
        // No API key configured = skip auth (development mode)
        return next();
    }

    if (!apiKey || apiKey !== validKey) {
        logger.warn('Invalid API key', { ip: req.ip, path: req.path, header: headerName });
        return res.status(401).json({ error: 'Invalid or missing API key' });
    }

    next();
}

/**
 * Rate limiting helper (simple in-memory implementation)
 */
const requestCounts = new Map();

export function rateLimit({ windowMs = 60000, maxRequests = 100 } = {}) {
    return (req, res, next) => {
        const key = req.ip;
        const now = Date.now();
        
        let record = requestCounts.get(key);
        if (!record || now - record.windowStart > windowMs) {
            record = { windowStart: now, count: 0 };
        }
        
        record.count++;
        requestCounts.set(key, record);

        if (record.count > maxRequests) {
            logger.warn('Rate limit exceeded', { ip: req.ip });
            return res.status(429).json({ 
                error: 'Too many requests',
                retryAfter: Math.ceil((record.windowStart + windowMs - now) / 1000)
            });
        }

        next();
    };
}
