import { NextResponse } from "next/server";
import fetch from "node-fetch";

// Configuration for the skillshift-ai backend
const SKILLSHIFT_AI_BASE_URL =
  process.env.SKILLSHIFT_AI_URL || "http://localhost:8000";

export async function GET(request, { params }) {
  try {
    const role = params.role;

    // Validate role parameter
    if (!role || role.trim().length === 0) {
      return NextResponse.json(
        { 
          success: false, 
          error: "Role parameter is required" 
        },
        { status: 400 }
      );
    }

    // Decode and sanitize role
    const decodedRole = decodeURIComponent(role).trim().toLowerCase();

    // Health check before processing
    try {
      const healthResponse = await fetch(
        `${SKILLSHIFT_AI_BASE_URL}/api/health-isolated`,
        {
          method: "GET",
          signal: AbortSignal.timeout(2000),
        }
      );

      if (!healthResponse.ok) {
        return NextResponse.json(
          {
            success: false,
            error: "Hero database service is currently unavailable",
            details: "Backend health check failed",
          },
          { status: 503 }
        );
      }
    } catch (healthError) {
      return NextResponse.json(
        {
          success: false,
          error: "Cannot connect to hero database service",
          details: "Please ensure the backend is running on port 8000",
        },
        { status: 503 }
      );
    }

    // Call the heroes by role endpoint
    const rolesResponse = await fetch(
      `${SKILLSHIFT_AI_BASE_URL}/api/hero-database/roles/${encodeURIComponent(decodedRole)}`,
      {
        method: "GET",
        signal: AbortSignal.timeout(10000), // 10 second timeout
      }
    );

    if (!rolesResponse.ok) {
      if (rolesResponse.status === 404) {
        const errorData = await rolesResponse.json();
        
        // Return available roles if hero search failed
        if (errorData.available_roles) {
          return NextResponse.json({
            success: false,
            error: "No heroes found for this role",
            role: decodedRole,
            available_roles: errorData.available_roles,
            metadata: {
              requested_role: decodedRole,
              timestamp: new Date().toISOString(),
              backend_url: SKILLSHIFT_AI_BASE_URL,
            },
          });
        }
      }

      const errorText = await rolesResponse.text();
      return NextResponse.json(
        {
          success: false,
          error: "Heroes by role lookup failed",
          details: errorText,
        },
        { status: rolesResponse.status }
      );
    }

    const rolesResult = await rolesResponse.json();

    // Transform response for frontend
    const dashboardResponse = {
      success: true,
      message: "Heroes by role retrieved successfully",
      role_info: {
        role: rolesResult.role || decodedRole,
        heroes: rolesResult.heroes || [],
        count: rolesResult.count || (rolesResult.heroes?.length || 0),
      },
      hero_details: (rolesResult.heroes || []).map(heroName => ({
        name: heroName,
        role: rolesResult.role || decodedRole,
        display_name: heroName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
      })),
      metadata: {
        requested_role: decodedRole,
        actual_role: rolesResult.role,
        hero_count: rolesResult.count || (rolesResult.heroes?.length || 0),
        timestamp: new Date().toISOString(),
        backend_url: SKILLSHIFT_AI_BASE_URL,
        roles_version: "2.0.0"
      },
    };

    return NextResponse.json(dashboardResponse);

  } catch (error) {
    console.error("Heroes by role API error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Heroes by role lookup failed",
        details: error.message,
        role: params.role,
      },
      { status: 500 }
    );
  }
}

export async function POST(request) {
  return NextResponse.json(
    { 
      success: false, 
      error: "POST method not supported. Use GET to retrieve heroes by role." 
    },
    { status: 405 }
  );
}