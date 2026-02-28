/**
 * SendGrid Email Provider
 * 
 * Handles transactional emails and serves as backup to Klaviyo.
 */

import sgMail from '@sendgrid/mail';
import sgClient from '@sendgrid/client';
import { logger } from '../utils/logger.js';

const SENDGRID_API_KEY = process.env.SENDGRID_API_KEY || '';
const SENDGRID_FROM_EMAIL = process.env.SENDGRID_FROM_EMAIL || 'noreply@careertrojan.com';
const SENDGRID_FROM_NAME = process.env.SENDGRID_FROM_NAME || 'CareerTrojan';

if (SENDGRID_API_KEY) {
    sgMail.setApiKey(SENDGRID_API_KEY);
    sgClient.setApiKey(SENDGRID_API_KEY);
}

/**
 * Check SendGrid API connection
 */
export async function checkSendgridConnection() {
    if (!SENDGRID_API_KEY) {
        return { connected: false, error: 'No API key configured' };
    }
    try {
        const [response] = await sgClient.request({
            method: 'GET',
            url: '/v3/user/profile'
        });
        return { connected: true, account: response.body.username };
    } catch (error) {
        logger.error('SendGrid connection check failed', { error: error.message });
        return { connected: false, error: error.message };
    }
}

/**
 * Send a simple email
 */
export async function sendEmail({ to, subject, text, html, replyTo, attachments = [] }) {
    const msg = {
        to,
        from: { email: SENDGRID_FROM_EMAIL, name: SENDGRID_FROM_NAME },
        subject,
        text: text || '',
        html: html || text || '',
        replyTo: replyTo || SENDGRID_FROM_EMAIL,
        attachments: attachments.map(att => ({
            content: att.content,
            filename: att.filename,
            type: att.type || 'application/octet-stream',
            disposition: 'attachment'
        }))
    };

    try {
        const [response] = await sgMail.send(msg);
        logger.info('SendGrid email sent', { to, subject, statusCode: response.statusCode });
        return { 
            success: true, 
            provider: 'sendgrid',
            messageId: response.headers['x-message-id']
        };
    } catch (error) {
        logger.error('SendGrid send failed', { to, subject, error: error.message });
        throw error;
    }
}

/**
 * Send email using a dynamic template
 */
export async function sendTemplateEmail({ to, templateId, dynamicData, subject }) {
    const msg = {
        to,
        from: { email: SENDGRID_FROM_EMAIL, name: SENDGRID_FROM_NAME },
        templateId,
        dynamicTemplateData: {
            ...dynamicData,
            subject: subject || dynamicData.subject
        }
    };

    try {
        const [response] = await sgMail.send(msg);
        logger.info('SendGrid template email sent', { to, templateId, statusCode: response.statusCode });
        return { 
            success: true, 
            provider: 'sendgrid',
            messageId: response.headers['x-message-id']
        };
    } catch (error) {
        logger.error('SendGrid template send failed', { to, templateId, error: error.message });
        throw error;
    }
}

/**
 * Send bulk emails (marketing/campaign)
 */
export async function sendBulkEmail(recipients, { subject, text, html, templateId, dynamicData }) {
    const messages = recipients.map(recipient => ({
        to: recipient.email,
        from: { email: SENDGRID_FROM_EMAIL, name: SENDGRID_FROM_NAME },
        subject: subject || dynamicData?.subject,
        ...(templateId ? {
            templateId,
            dynamicTemplateData: { ...dynamicData, ...recipient.data }
        } : {
            text: text || '',
            html: html || text || ''
        })
    }));

    try {
        // SendGrid allows up to 1000 emails per API call
        const batchSize = 1000;
        const results = [];
        
        for (let i = 0; i < messages.length; i += batchSize) {
            const batch = messages.slice(i, i + batchSize);
            const [response] = await sgMail.send(batch);
            results.push({
                batch: Math.floor(i / batchSize) + 1,
                count: batch.length,
                statusCode: response.statusCode
            });
        }

        logger.info('SendGrid bulk send complete', { totalRecipients: recipients.length });
        return { success: true, provider: 'sendgrid', batches: results };
    } catch (error) {
        logger.error('SendGrid bulk send failed', { error: error.message });
        throw error;
    }
}

/**
 * Add contact to SendGrid Marketing list
 */
export async function addContact(email, listIds = [], customFields = {}) {
    try {
        const [response] = await sgClient.request({
            method: 'PUT',
            url: '/v3/marketing/contacts',
            body: {
                list_ids: listIds,
                contacts: [{
                    email,
                    ...customFields
                }]
            }
        });
        logger.info('SendGrid contact added', { email });
        return { success: true, jobId: response.body.job_id };
    } catch (error) {
        logger.error('SendGrid add contact failed', { email, error: error.message });
        throw error;
    }
}

/**
 * Get email statistics
 */
export async function getStats(startDate, endDate) {
    try {
        const [response] = await sgClient.request({
            method: 'GET',
            url: '/v3/stats',
            qs: {
                start_date: startDate,
                end_date: endDate
            }
        });
        return response.body;
    } catch (error) {
        logger.error('SendGrid get stats failed', { error: error.message });
        throw error;
    }
}

export default {
    checkSendgridConnection,
    sendEmail,
    sendTemplateEmail,
    sendBulkEmail,
    addContact,
    getStats
};
