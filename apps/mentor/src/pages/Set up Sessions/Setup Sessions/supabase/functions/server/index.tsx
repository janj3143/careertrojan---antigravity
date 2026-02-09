import { Hono } from "npm:hono";
import { cors } from "npm:hono/cors";
import { logger } from "npm:hono/logger";
import * as kv from "./kv_store.tsx";
import { createClient } from "npm:@supabase/supabase-js@2";
import * as OTPAuth from "npm:otpauth@9";

const app = new Hono();

// Initialize Supabase client
const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
);

// Enable logger
app.use('*', logger(console.log));

// Enable CORS for all routes and methods
app.use(
  "/*",
  cors({
    origin: "*",
    allowHeaders: ["Content-Type", "Authorization"],
    allowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    exposeHeaders: ["Content-Length"],
    maxAge: 600,
  }),
);

// Health check endpoint
app.get("/make-server-f4611869/health", (c) => {
  return c.json({ status: "ok" });
});

// ============ AUTH ROUTES ============

// Sign up route
app.post("/make-server-f4611869/auth/signup", async (c) => {
  try {
    const { email, password, name, role } = await c.req.json();
    
    if (!email || !password || !name || !role) {
      return c.json({ error: "Email, password, name, and role are required" }, 400);
    }

    const { data, error } = await supabase.auth.admin.createUser({
      email,
      password,
      user_metadata: { name, role },
      // Automatically confirm the user's email since an email server hasn't been configured.
      email_confirm: true
    });

    if (error) {
      console.log(`Signup error: ${error.message}`);
      return c.json({ error: error.message }, 400);
    }

    // Store user profile
    await kv.set(`user:${data.user.id}`, {
      id: data.user.id,
      email,
      name,
      role,
      created_at: new Date().toISOString()
    });

    // If mentor, generate 2FA secret
    if (role === "mentor") {
      const secret = new OTPAuth.Secret({ size: 20 });
      const totp = new OTPAuth.TOTP({
        issuer: "Sessions Calendar",
        label: email,
        algorithm: "SHA1",
        digits: 6,
        period: 30,
        secret: secret,
      });

      // Generate QR code as data URL
      const qrCode = totp.toString();
      
      // Store 2FA secret (not yet enabled)
      await kv.set(`2fa:${data.user.id}`, {
        secret: secret.base32,
        enabled: false,
        created_at: new Date().toISOString()
      });

      return c.json({ 
        user: data.user,
        twoFactor: {
          secret: secret.base32,
          qrCode: qrCode,
          userId: data.user.id
        }
      });
    }

    return c.json({ user: data.user });
  } catch (error) {
    console.log(`Signup exception: ${error}`);
    return c.json({ error: "Internal server error during signup" }, 500);
  }
});

// Verify 2FA setup
app.post("/make-server-f4611869/auth/verify-2fa", async (c) => {
  try {
    const { userId, token } = await c.req.json();
    
    if (!userId || !token) {
      return c.json({ error: "User ID and token are required" }, 400);
    }

    const twoFactorData = await kv.get(`2fa:${userId}`);
    if (!twoFactorData) {
      return c.json({ error: "2FA not set up for this user" }, 404);
    }

    const secret = OTPAuth.Secret.fromBase32(twoFactorData.secret);
    const totp = new OTPAuth.TOTP({
      issuer: "Sessions Calendar",
      label: userId,
      algorithm: "SHA1",
      digits: 6,
      period: 30,
      secret: secret,
    });

    const delta = totp.validate({ token, window: 1 });
    
    if (delta === null) {
      return c.json({ error: "Invalid 2FA code" }, 400);
    }

    // Enable 2FA
    twoFactorData.enabled = true;
    twoFactorData.verified_at = new Date().toISOString();
    await kv.set(`2fa:${userId}`, twoFactorData);

    return c.json({ success: true });
  } catch (error) {
    console.log(`2FA verification error: ${error}`);
    return c.json({ error: "Internal server error during 2FA verification" }, 500);
  }
});

// Check if user has 2FA enabled
app.post("/make-server-f4611869/auth/check-2fa", async (c) => {
  try {
    const { email } = await c.req.json();
    
    if (!email) {
      return c.json({ error: "Email is required" }, 400);
    }

    // Get user by email
    const users = await kv.getByPrefix("user:");
    const user = users?.find((u: any) => u.email === email);
    
    if (!user) {
      return c.json({ requires2FA: false });
    }

    const twoFactorData = await kv.get(`2fa:${user.id}`);
    
    return c.json({ 
      requires2FA: twoFactorData?.enabled === true,
      role: user.role
    });
  } catch (error) {
    console.log(`Check 2FA error: ${error}`);
    return c.json({ error: "Internal server error checking 2FA" }, 500);
  }
});

// Validate 2FA token during login
app.post("/make-server-f4611869/auth/validate-2fa", async (c) => {
  try {
    const { email, token } = await c.req.json();
    
    if (!email || !token) {
      return c.json({ error: "Email and token are required" }, 400);
    }

    // Get user by email
    const users = await kv.getByPrefix("user:");
    const user = users?.find((u: any) => u.email === email);
    
    if (!user) {
      return c.json({ error: "User not found" }, 404);
    }

    const twoFactorData = await kv.get(`2fa:${user.id}`);
    if (!twoFactorData || !twoFactorData.enabled) {
      return c.json({ error: "2FA not enabled for this user" }, 400);
    }

    const secret = OTPAuth.Secret.fromBase32(twoFactorData.secret);
    const totp = new OTPAuth.TOTP({
      issuer: "Sessions Calendar",
      label: email,
      algorithm: "SHA1",
      digits: 6,
      period: 30,
      secret: secret,
    });

    const delta = totp.validate({ token, window: 1 });
    
    if (delta === null) {
      return c.json({ error: "Invalid 2FA code" }, 400);
    }

    return c.json({ success: true });
  } catch (error) {
    console.log(`Validate 2FA error: ${error}`);
    return c.json({ error: "Internal server error validating 2FA" }, 500);
  }
});

// ============ SESSION ROUTES ============

// Get all sessions for a user
app.get("/make-server-f4611869/sessions", async (c) => {
  try {
    const accessToken = c.req.header("Authorization")?.split(" ")[1];
    const { data: { user }, error: authError } = await supabase.auth.getUser(accessToken);
    
    if (!user || authError) {
      return c.json({ error: "Unauthorized" }, 401);
    }

    // Get user profile to determine role
    const userProfile = await kv.get(`user:${user.id}`);
    if (!userProfile) {
      return c.json({ error: "User profile not found" }, 404);
    }

    // Get all sessions
    const sessionKeys = await kv.getByPrefix("session:");
    let sessions = sessionKeys || [];

    // Filter sessions based on role
    if (userProfile.role === "mentor") {
      sessions = sessions.filter((s: any) => s.mentor_id === user.id);
    } else {
      sessions = sessions.filter((s: any) => s.mentee_id === user.id);
    }

    return c.json({ sessions });
  } catch (error) {
    console.log(`Get sessions error: ${error}`);
    return c.json({ error: "Internal server error while fetching sessions" }, 500);
  }
});

// Create a new session
app.post("/make-server-f4611869/sessions", async (c) => {
  try {
    const accessToken = c.req.header("Authorization")?.split(" ")[1];
    const { data: { user }, error: authError } = await supabase.auth.getUser(accessToken);
    
    if (!user || authError) {
      return c.json({ error: "Unauthorized" }, 401);
    }

    const { mentee_name, package_name, start_time, duration_minutes } = await c.req.json();
    
    if (!mentee_name || !package_name || !start_time || !duration_minutes) {
      return c.json({ error: "Missing required fields" }, 400);
    }

    const sessionId = `session:${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const startDate = new Date(start_time);
    const endDate = new Date(startDate.getTime() + duration_minutes * 60000);

    const session = {
      id: sessionId,
      mentor_id: user.id,
      mentee_id: null,
      mentee_name,
      package_name,
      start_time: startDate.toISOString(),
      end_time: endDate.toISOString(),
      duration_minutes,
      status: "pending",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    await kv.set(sessionId, session);

    // Log activity
    await kv.set(`activity:${Date.now()}`, {
      user_id: user.id,
      action: "session_created",
      details: `Session added for ${mentee_name} (${package_name})`,
      timestamp: new Date().toISOString()
    });

    return c.json({ session });
  } catch (error) {
    console.log(`Create session error: ${error}`);
    return c.json({ error: "Internal server error while creating session" }, 500);
  }
});

// Update session status
app.patch("/make-server-f4611869/sessions/:id", async (c) => {
  try {
    const accessToken = c.req.header("Authorization")?.split(" ")[1];
    const { data: { user }, error: authError } = await supabase.auth.getUser(accessToken);
    
    if (!user || authError) {
      return c.json({ error: "Unauthorized" }, 401);
    }

    const sessionId = c.req.param("id");
    const { status } = await c.req.json();

    if (!status) {
      return c.json({ error: "Status is required" }, 400);
    }

    const session = await kv.get(sessionId);
    if (!session) {
      return c.json({ error: "Session not found" }, 404);
    }

    // Check if user owns this session
    if (session.mentor_id !== user.id) {
      return c.json({ error: "Forbidden" }, 403);
    }

    session.status = status;
    session.updated_at = new Date().toISOString();
    await kv.set(sessionId, session);

    // Log activity
    await kv.set(`activity:${Date.now()}`, {
      user_id: user.id,
      action: "session_updated",
      details: `Session ${status} for ${session.mentee_name}`,
      timestamp: new Date().toISOString()
    });

    return c.json({ session });
  } catch (error) {
    console.log(`Update session error: ${error}`);
    return c.json({ error: "Internal server error while updating session" }, 500);
  }
});

// Delete a session
app.delete("/make-server-f4611869/sessions/:id", async (c) => {
  try {
    const accessToken = c.req.header("Authorization")?.split(" ")[1];
    const { data: { user }, error: authError } = await supabase.auth.getUser(accessToken);
    
    if (!user || authError) {
      return c.json({ error: "Unauthorized" }, 401);
    }

    const sessionId = c.req.param("id");
    const session = await kv.get(sessionId);
    
    if (!session) {
      return c.json({ error: "Session not found" }, 404);
    }

    if (session.mentor_id !== user.id) {
      return c.json({ error: "Forbidden" }, 403);
    }

    await kv.del(sessionId);

    // Log activity
    await kv.set(`activity:${Date.now()}`, {
      user_id: user.id,
      action: "session_deleted",
      details: `Session canceled for ${session.mentee_name}`,
      timestamp: new Date().toISOString()
    });

    return c.json({ success: true });
  } catch (error) {
    console.log(`Delete session error: ${error}`);
    return c.json({ error: "Internal server error while deleting session" }, 500);
  }
});

// Get activity log
app.get("/make-server-f4611869/activities", async (c) => {
  try {
    const accessToken = c.req.header("Authorization")?.split(" ")[1];
    const { data: { user }, error: authError } = await supabase.auth.getUser(accessToken);
    
    if (!user || authError) {
      return c.json({ error: "Unauthorized" }, 401);
    }

    const activities = await kv.getByPrefix("activity:");
    const userActivities = (activities || [])
      .filter((a: any) => a.user_id === user.id)
      .sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 30);

    return c.json({ activities: userActivities });
  } catch (error) {
    console.log(`Get activities error: ${error}`);
    return c.json({ error: "Internal server error while fetching activities" }, 500);
  }
});

Deno.serve(app.fetch);