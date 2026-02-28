/**
 * SendGrid API Routes
 */

import { Router } from 'express';
import { 
    sendEmail, 
    sendTemplateEmail, 
    sendBulkEmail,
    addContact,
    getStats 
} from '../providers/sendgrid.js';
import { validateRequest } from '../middleware/validate.js';
import Joi from 'joi';

export const sendgridRouter = Router();

// Validation schemas
const emailSchema = Joi.object({
    to: Joi.alternatives().try(
        Joi.string().email(),
        Joi.array().items(Joi.string().email())
    ).required(),
    subject: Joi.string().required(),
    text: Joi.string(),
    html: Joi.string(),
    replyTo: Joi.string().email(),
    attachments: Joi.array().items(Joi.object({
        content: Joi.string().required(),
        filename: Joi.string().required(),
        type: Joi.string()
    }))
});

const templateSchema = Joi.object({
    to: Joi.string().email().required(),
    templateId: Joi.string().required(),
    dynamicData: Joi.object(),
    subject: Joi.string()
});

// Send simple email
sendgridRouter.post('/send', validateRequest(emailSchema), async (req, res) => {
    try {
        const result = await sendEmail(req.body);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Send template email
sendgridRouter.post('/template', validateRequest(templateSchema), async (req, res) => {
    try {
        const result = await sendTemplateEmail(req.body);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Send bulk emails
sendgridRouter.post('/bulk', async (req, res) => {
    try {
        const { recipients, subject, text, html, templateId, dynamicData } = req.body;
        
        if (!recipients || !Array.isArray(recipients) || recipients.length === 0) {
            return res.status(400).json({ error: 'recipients array required' });
        }

        const result = await sendBulkEmail(recipients, { subject, text, html, templateId, dynamicData });
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Add contact to marketing lists
sendgridRouter.post('/contacts', async (req, res) => {
    try {
        const { email, listIds, customFields } = req.body;
        if (!email) {
            return res.status(400).json({ error: 'email required' });
        }
        const result = await addContact(email, listIds, customFields);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get email statistics
sendgridRouter.get('/stats', async (req, res) => {
    try {
        const { startDate, endDate } = req.query;
        const today = new Date().toISOString().split('T')[0];
        const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        
        const stats = await getStats(startDate || weekAgo, endDate || today);
        res.json({ stats });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});
