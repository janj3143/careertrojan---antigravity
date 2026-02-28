/**
 * Klaviyo Email Provider
 * 
 * Handles marketing campaigns, user engagement, and list management.
 */

import { ApiClient, ProfilesApi, EventsApi, ListsApi, CampaignsApi } from 'klaviyo-api';
import { logger } from '../utils/logger.js';

const KLAVIYO_API_KEY = process.env.KLAVIYO_API_KEY || '';

// Configure API client
if (KLAVIYO_API_KEY) {
    ApiClient.instance.authentications['Klaviyo-API-Key'].apiKey = KLAVIYO_API_KEY;
}

const profilesApi = new ProfilesApi();
const eventsApi = new EventsApi();
const listsApi = new ListsApi();
const campaignsApi = new CampaignsApi();

/**
 * Check Klaviyo API connection
 */
export async function checkKlaviyoConnection() {
    if (!KLAVIYO_API_KEY) {
        return { connected: false, error: 'No API key configured' };
    }
    try {
        // Simple API call to verify connection
        await listsApi.getLists({ pageSize: 1 });
        return { connected: true };
    } catch (error) {
        logger.error('Klaviyo connection check failed', { error: error.message });
        return { connected: false, error: error.message };
    }
}

/**
 * Create or update a profile in Klaviyo
 */
export async function upsertProfile(profileData) {
    const { email, firstName, lastName, phone, properties = {} } = profileData;
    
    try {
        const profile = await profilesApi.createOrUpdateProfile({
            data: {
                type: 'profile',
                attributes: {
                    email,
                    first_name: firstName,
                    last_name: lastName,
                    phone_number: phone,
                    properties: {
                        ...properties,
                        source: 'careertrojan',
                        updated_at: new Date().toISOString()
                    }
                }
            }
        });
        logger.info('Klaviyo profile upserted', { email });
        return { success: true, profileId: profile.data.id };
    } catch (error) {
        logger.error('Klaviyo profile upsert failed', { email, error: error.message });
        throw error;
    }
}

/**
 * Track an event for a profile
 */
export async function trackEvent(email, eventName, eventProperties = {}) {
    try {
        await eventsApi.createEvent({
            data: {
                type: 'event',
                attributes: {
                    metric: { data: { type: 'metric', attributes: { name: eventName } } },
                    profile: { data: { type: 'profile', attributes: { email } } },
                    properties: {
                        ...eventProperties,
                        timestamp: new Date().toISOString()
                    }
                }
            }
        });
        logger.info('Klaviyo event tracked', { email, eventName });
        return { success: true };
    } catch (error) {
        logger.error('Klaviyo event tracking failed', { email, eventName, error: error.message });
        throw error;
    }
}

/**
 * Add profile to a list
 */
export async function addToList(listId, email) {
    try {
        await listsApi.createListRelationshipsProfile(listId, {
            data: [{ type: 'profile', attributes: { email } }]
        });
        logger.info('Profile added to Klaviyo list', { email, listId });
        return { success: true };
    } catch (error) {
        logger.error('Add to Klaviyo list failed', { email, listId, error: error.message });
        throw error;
    }
}

/**
 * Get all lists
 */
export async function getLists() {
    try {
        const response = await listsApi.getLists();
        return response.data.map(list => ({
            id: list.id,
            name: list.attributes.name,
            created: list.attributes.created
        }));
    } catch (error) {
        logger.error('Get Klaviyo lists failed', { error: error.message });
        throw error;
    }
}

/**
 * Trigger a flow for a profile (e.g., welcome series, mentor intro)
 */
export async function triggerFlow(email, flowTriggerEvent, properties = {}) {
    return trackEvent(email, flowTriggerEvent, {
        ...properties,
        flow_trigger: true
    });
}

/**
 * Send transactional email via Klaviyo (requires transactional email feature)
 */
export async function sendTransactional(templateId, recipientEmail, dynamicData = {}) {
    // Note: Klaviyo transactional email requires specific setup
    // This uses the Events API to trigger template-based flows
    try {
        await trackEvent(recipientEmail, `Transactional_${templateId}`, {
            template_id: templateId,
            ...dynamicData
        });
        logger.info('Klaviyo transactional triggered', { recipientEmail, templateId });
        return { success: true, provider: 'klaviyo' };
    } catch (error) {
        logger.error('Klaviyo transactional failed', { recipientEmail, templateId, error: error.message });
        throw error;
    }
}

export default {
    checkKlaviyoConnection,
    upsertProfile,
    trackEvent,
    addToList,
    getLists,
    triggerFlow,
    sendTransactional
};
