/**
 * Mentor-User Email Communication System
 * 
 * Handles all email communication between mentors and users:
 * - Introduction emails
 * - Session reminders
 * - Feedback requests
 * - Document sharing
 * - Scheduling notifications
 */

import { Router } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { logger } from '../utils/logger.js';
import { sendEmail, sendTemplateEmail } from '../providers/sendgrid.js';
import { upsertProfile, trackEvent, triggerFlow } from '../providers/klaviyo.js';
import { createTicket } from '../providers/zendesk.js';
import Handlebars from 'handlebars';

export const mentorRouter = Router();

// Email templates (in production, load from database or file system)
const TEMPLATES = {
    mentorIntro: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #0D9488;">🎉 You've Been Matched with a Mentor!</h2>
            <p>Hi {{userName}},</p>
            <p>Great news! You've been matched with <strong>{{mentorName}}</strong> as your career mentor.</p>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3 style="margin-top: 0;">About Your Mentor</h3>
                <p><strong>{{mentorName}}</strong></p>
                <p>{{mentorTitle}} at {{mentorCompany}}</p>
                <p style="color: #666;">{{mentorBio}}</p>
            </div>
            <p>{{mentorName}} will reach out to schedule your first session soon.</p>
            <a href="{{portalUrl}}" style="display: inline-block; padding: 12px 24px; background: #0D9488; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">
                View in Portal
            </a>
            <p style="margin-top: 30px; color: #666; font-size: 14px;">
                Questions? Reply to this email or contact support.
            </p>
        </div>
    `,
    sessionReminder: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #0D9488;">📅 Session Reminder</h2>
            <p>Hi {{recipientName}},</p>
            <p>This is a reminder about your upcoming mentoring session:</p>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <p><strong>📆 Date:</strong> {{sessionDate}}</p>
                <p><strong>⏰ Time:</strong> {{sessionTime}}</p>
                <p><strong>👤 With:</strong> {{otherPartyName}}</p>
                <p><strong>📍 Location:</strong> {{sessionLocation}}</p>
                {{#if sessionAgenda}}
                <p><strong>📋 Agenda:</strong> {{sessionAgenda}}</p>
                {{/if}}
            </div>
            <a href="{{sessionLink}}" style="display: inline-block; padding: 12px 24px; background: #0D9488; color: white; text-decoration: none; border-radius: 5px;">
                Join Session
            </a>
        </div>
    `,
    feedbackRequest: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #0D9488;">💬 How was your session?</h2>
            <p>Hi {{userName}},</p>
            <p>We hope your session with {{mentorName}} went well!</p>
            <p>Your feedback helps us improve the mentoring experience:</p>
            <div style="text-align: center; margin: 30px 0;">
                {{responseButtons}}
            </div>
            <p style="color: #666; font-size: 14px;">Click a rating above to provide quick feedback.</p>
        </div>
    `,
    documentShared: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #0D9488;">📄 Document Shared</h2>
            <p>Hi {{recipientName}},</p>
            <p><strong>{{senderName}}</strong> has shared a document with you:</p>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <p><strong>📄 {{documentName}}</strong></p>
                {{#if documentDescription}}
                <p style="color: #666;">{{documentDescription}}</p>
                {{/if}}
            </div>
            <a href="{{documentUrl}}" style="display: inline-block; padding: 12px 24px; background: #0D9488; color: white; text-decoration: none; border-radius: 5px;">
                View Document
            </a>
        </div>
    `
};

// Compile Handlebars templates
const compiledTemplates = {};
for (const [name, template] of Object.entries(TEMPLATES)) {
    compiledTemplates[name] = Handlebars.compile(template);
}

/**
 * Send mentor introduction email to user
 * POST /api/email/mentor/intro
 */
mentorRouter.post('/intro', async (req, res) => {
    try {
        const {
            userId,
            userEmail,
            userName,
            mentorId,
            mentorEmail,
            mentorName,
            mentorTitle,
            mentorCompany,
            mentorBio
        } = req.body;

        if (!userEmail || !mentorEmail || !userName || !mentorName) {
            return res.status(400).json({ 
                error: 'userEmail, userEmail, userName, mentorName required' 
            });
        }

        const portalUrl = `${process.env.USER_PORTAL_URL || 'http://localhost:8602'}/mentor`;

        // Send to user
        const userHtml = compiledTemplates.mentorIntro({
            userName,
            mentorName,
            mentorTitle: mentorTitle || 'Career Mentor',
            mentorCompany: mentorCompany || '',
            mentorBio: mentorBio || 'Looking forward to helping you achieve your career goals!',
            portalUrl
        });

        const userResult = await sendEmail({
            to: userEmail,
            subject: `🎉 Meet your mentor: ${mentorName}`,
            html: userHtml
        });

        // Track in Klaviyo
        try {
            await trackEvent(userEmail, 'Mentor_Matched', {
                mentorId,
                mentorName,
                matchedAt: new Date().toISOString()
            });
            await trackEvent(mentorEmail, 'Assigned_Mentee', {
                userId,
                userName,
                matchedAt: new Date().toISOString()
            });
        } catch (e) {
            logger.warn('Klaviyo tracking failed', { error: e.message });
        }

        logger.info('Mentor intro email sent', { userEmail, mentorEmail });

        res.json({
            success: true,
            userEmailSent: true,
            messageId: userResult.messageId
        });
    } catch (error) {
        logger.error('Mentor intro email failed', { error: error.message });
        res.status(500).json({ error: error.message });
    }
});

/**
 * Send session reminder to both parties
 * POST /api/email/mentor/session-reminder
 */
mentorRouter.post('/session-reminder', async (req, res) => {
    try {
        const {
            sessionId,
            sessionDate,
            sessionTime,
            sessionLocation,
            sessionLink,
            sessionAgenda,
            user: { email: userEmail, name: userName },
            mentor: { email: mentorEmail, name: mentorName }
        } = req.body;

        if (!userEmail || !mentorEmail || !sessionDate) {
            return res.status(400).json({ error: 'user, mentor, sessionDate required' });
        }

        const results = [];

        // Send to user
        const userHtml = compiledTemplates.sessionReminder({
            recipientName: userName,
            sessionDate,
            sessionTime,
            otherPartyName: mentorName,
            sessionLocation: sessionLocation || 'Video Call',
            sessionLink: sessionLink || '#',
            sessionAgenda
        });

        const userResult = await sendEmail({
            to: userEmail,
            subject: `📅 Reminder: Session with ${mentorName}`,
            html: userHtml
        });
        results.push({ recipient: 'user', ...userResult });

        // Send to mentor
        const mentorHtml = compiledTemplates.sessionReminder({
            recipientName: mentorName,
            sessionDate,
            sessionTime,
            otherPartyName: userName,
            sessionLocation: sessionLocation || 'Video Call',
            sessionLink: sessionLink || '#',
            sessionAgenda
        });

        const mentorResult = await sendEmail({
            to: mentorEmail,
            subject: `📅 Reminder: Session with ${userName}`,
            html: mentorHtml
        });
        results.push({ recipient: 'mentor', ...mentorResult });

        // Track events
        try {
            await trackEvent(userEmail, 'Session_Reminder_Sent', { sessionId, sessionDate });
            await trackEvent(mentorEmail, 'Session_Reminder_Sent', { sessionId, sessionDate });
        } catch (e) {
            logger.warn('Klaviyo tracking failed', { error: e.message });
        }

        logger.info('Session reminders sent', { sessionId, userEmail, mentorEmail });

        res.json({ success: true, results });
    } catch (error) {
        logger.error('Session reminder failed', { error: error.message });
        res.status(500).json({ error: error.message });
    }
});

/**
 * Send feedback request after session
 * POST /api/email/mentor/feedback-request
 */
mentorRouter.post('/feedback-request', async (req, res) => {
    try {
        const {
            sessionId,
            userEmail,
            userName,
            mentorName,
            feedbackUrl
        } = req.body;

        if (!userEmail || !userName || !mentorName) {
            return res.status(400).json({ error: 'userEmail, userName, mentorName required' });
        }

        const BASE_URL = process.env.EMAIL_SERVICE_BASE_URL || 'http://localhost:3050';
        
        // Create quick feedback buttons
        const ratings = ['⭐⭐⭐⭐⭐ Excellent', '⭐⭐⭐⭐ Good', '⭐⭐⭐ Okay', '⭐⭐ Could improve'];
        const buttons = ratings.map(rating => {
            const encodedRating = encodeURIComponent(rating);
            return `<a href="${feedbackUrl || BASE_URL}?rating=${encodedRating}&session=${sessionId}" 
                       style="display: block; padding: 10px 20px; margin: 5px; background: #0D9488; color: white; text-decoration: none; border-radius: 5px; text-align: center;">
                ${rating}
            </a>`;
        }).join('');

        const html = compiledTemplates.feedbackRequest({
            userName,
            mentorName,
            responseButtons: buttons
        });

        const result = await sendEmail({
            to: userEmail,
            subject: `💬 How was your session with ${mentorName}?`,
            html
        });

        // Track
        try {
            await trackEvent(userEmail, 'Feedback_Request_Sent', { sessionId, mentorName });
        } catch (e) {
            logger.warn('Klaviyo tracking failed', { error: e.message });
        }

        logger.info('Feedback request sent', { userEmail, sessionId });

        res.json({ success: true, ...result });
    } catch (error) {
        logger.error('Feedback request failed', { error: error.message });
        res.status(500).json({ error: error.message });
    }
});

/**
 * Send document shared notification
 * POST /api/email/mentor/document-shared
 */
mentorRouter.post('/document-shared', async (req, res) => {
    try {
        const {
            recipientEmail,
            recipientName,
            senderName,
            documentName,
            documentDescription,
            documentUrl
        } = req.body;

        if (!recipientEmail || !senderName || !documentName || !documentUrl) {
            return res.status(400).json({ 
                error: 'recipientEmail, senderName, documentName, documentUrl required' 
            });
        }

        const html = compiledTemplates.documentShared({
            recipientName: recipientName || recipientEmail.split('@')[0],
            senderName,
            documentName,
            documentDescription,
            documentUrl
        });

        const result = await sendEmail({
            to: recipientEmail,
            subject: `📄 ${senderName} shared a document with you`,
            html
        });

        // Track
        try {
            await trackEvent(recipientEmail, 'Document_Shared', { 
                senderName, 
                documentName 
            });
        } catch (e) {
            logger.warn('Klaviyo tracking failed', { error: e.message });
        }

        logger.info('Document shared email sent', { recipientEmail, documentName });

        res.json({ success: true, ...result });
    } catch (error) {
        logger.error('Document shared email failed', { error: error.message });
        res.status(500).json({ error: error.message });
    }
});

/**
 * Escalate a mentor-user issue to support
 * POST /api/email/mentor/escalate
 */
mentorRouter.post('/escalate', async (req, res) => {
    try {
        const {
            reporterEmail,
            reporterName,
            issueType,     // 'mentor-issue', 'user-issue', 'scheduling', 'other'
            subject,
            description,
            relatedUserId,
            relatedMentorId
        } = req.body;

        if (!reporterEmail || !issueType || !description) {
            return res.status(400).json({ 
                error: 'reporterEmail, issueType, description required' 
            });
        }

        // Create Zendesk ticket
        const ticket = await createTicket({
            requesterEmail: reporterEmail,
            requesterName: reporterName,
            subject: subject || `Mentor Program Issue: ${issueType}`,
            body: description,
            priority: 'high',
            tags: ['mentor-program', issueType],
            customFields: {
                relatedUserId,
                relatedMentorId
            }
        });

        // Track
        try {
            await trackEvent(reporterEmail, 'Mentor_Issue_Escalated', { 
                issueType, 
                ticketId: ticket.ticketId 
            });
        } catch (e) {
            logger.warn('Klaviyo tracking failed', { error: e.message });
        }

        logger.info('Mentor issue escalated', { reporterEmail, ticketId: ticket.ticketId });

        res.json({ success: true, ...ticket });
    } catch (error) {
        logger.error('Escalation failed', { error: error.message });
        res.status(500).json({ error: error.message });
    }
});

/**
 * Bulk notify all mentors (e.g., announcements)
 * POST /api/email/mentor/broadcast
 */
mentorRouter.post('/broadcast', async (req, res) => {
    try {
        const {
            recipients,  // Array of { email, name }
            subject,
            bodyHtml,
            bodyText
        } = req.body;

        if (!recipients || !Array.isArray(recipients) || !subject) {
            return res.status(400).json({ error: 'recipients array and subject required' });
        }

        const results = [];
        const errors = [];

        for (const recipient of recipients) {
            try {
                const result = await sendEmail({
                    to: recipient.email,
                    subject,
                    html: bodyHtml?.replace('{{name}}', recipient.name || ''),
                    text: bodyText?.replace('{{name}}', recipient.name || '')
                });
                results.push({ email: recipient.email, success: true });
            } catch (e) {
                errors.push({ email: recipient.email, error: e.message });
            }
        }

        logger.info('Mentor broadcast complete', { 
            total: recipients.length, 
            sent: results.length, 
            failed: errors.length 
        });

        res.json({ 
            success: errors.length === 0,
            sent: results.length,
            failed: errors.length,
            errors: errors.length > 0 ? errors : undefined
        });
    } catch (error) {
        logger.error('Broadcast failed', { error: error.message });
        res.status(500).json({ error: error.message });
    }
});
