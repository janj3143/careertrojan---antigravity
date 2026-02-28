/**
 * Klaviyo API Routes
 */

import { Router } from 'express';
import { 
    upsertProfile, 
    trackEvent, 
    addToList, 
    getLists,
    triggerFlow,
    sendTransactional 
} from '../providers/klaviyo.js';
import { validateRequest } from '../middleware/validate.js';
import Joi from 'joi';

export const klaviyoRouter = Router();

// Validation schemas
const profileSchema = Joi.object({
    email: Joi.string().email().required(),
    firstName: Joi.string().allow(''),
    lastName: Joi.string().allow(''),
    phone: Joi.string().allow(''),
    properties: Joi.object()
});

const eventSchema = Joi.object({
    email: Joi.string().email().required(),
    eventName: Joi.string().required(),
    properties: Joi.object()
});

// Upsert profile
klaviyoRouter.post('/profile', validateRequest(profileSchema), async (req, res) => {
    try {
        const result = await upsertProfile(req.body);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Track event
klaviyoRouter.post('/event', validateRequest(eventSchema), async (req, res) => {
    try {
        const { email, eventName, properties } = req.body;
        const result = await trackEvent(email, eventName, properties);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get lists
klaviyoRouter.get('/lists', async (req, res) => {
    try {
        const lists = await getLists();
        res.json({ lists });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Add to list
klaviyoRouter.post('/lists/:listId/subscribe', async (req, res) => {
    try {
        const { email } = req.body;
        if (!email) {
            return res.status(400).json({ error: 'email required' });
        }
        const result = await addToList(req.params.listId, email);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Trigger flow
klaviyoRouter.post('/flow/trigger', async (req, res) => {
    try {
        const { email, flowEvent, properties } = req.body;
        if (!email || !flowEvent) {
            return res.status(400).json({ error: 'email and flowEvent required' });
        }
        const result = await triggerFlow(email, flowEvent, properties);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Send transactional (via flow trigger)
klaviyoRouter.post('/transactional', async (req, res) => {
    try {
        const { templateId, recipientEmail, data } = req.body;
        if (!templateId || !recipientEmail) {
            return res.status(400).json({ error: 'templateId and recipientEmail required' });
        }
        const result = await sendTransactional(templateId, recipientEmail, data);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});
