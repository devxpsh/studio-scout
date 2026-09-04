import type { ShootPlan } from "../types";

export const sampleShootPlan: ShootPlan = {
  title: "The Last Departure",
  shoot_plan_notes: "3 conflicts detected: 1 blocker(s), 2 warning(s), 0 info.",
  global_conflicts: [
    {
      type: "continuity",
      affected_scenes: [1, 4],
      description:
        "Scenes sharing location 'old railway station' have different top-ranked candidates: Coastal Junction Depot, Heritage Rail Platform.",
      severity: "warning",
      suggested_resolution:
        "Pick one candidate for all scenes at this location to preserve continuity.",
    },
  ],
  scenes: [
    {
      scene_number: 1,
      location: "old railway station",
      recommended: "Heritage Rail Platform",
      rationale:
        "Heritage Rail Platform offers the strongest visual match for a working-era station with minimal modern signage, and has prior film-permit history.",
      top_candidates: [
        {
          candidate: {
            name: "Heritage Rail Platform",
            address_or_area: "Old Town Junction, Sector 4",
            description:
              "A preserved early-20th-century platform still in limited use, with period-accurate signage and architecture.",
            evidence: [
              {
                source_url: "https://example.com/heritage-rail-platform",
                source_title:
                  "Heritage Rail Platform — Regional Film Office listing",
                snippet:
                  "Available for film bookings with 5-day advance notice.",
              },
            ],
          },
          score: {
            visual_match: 95,
            feasibility: 90,
            logistics: 80,
            cost_fit: 70,
            permit_ease: 85,
            evidence_confidence: 90,
          },
          composite_score: 86.5,
        },
        {
          candidate: {
            name: "Coastal Junction Depot",
            address_or_area: "Coastal Line, Mile 12",
            description:
              "A smaller, less ornate depot with a coastal backdrop.",
            evidence: [],
          },
          score: {
            visual_match: 80,
            feasibility: 75,
            logistics: 70,
            cost_fit: 60,
            permit_ease: 70,
            evidence_confidence: 50,
          },
          composite_score: 71.75,
        },
      ],
      conflicts: [],
    },
    {
      scene_number: 2,
      location: "detective office",
      recommended: "none found",
      rationale: "",
      top_candidates: [],
      conflicts: [
        {
          type: "low_confidence",
          affected_scenes: [2],
          description:
            "No grounded candidates were returned for this scene during research.",
          severity: "blocker",
          suggested_resolution:
            "Source this location manually before finalizing the shoot plan.",
        },
      ],
    },
    {
      scene_number: 3,
      location: "coastal road",
      recommended: "Windward Cliff Road",
      rationale:
        "Windward Cliff Road matches the scene\u2019s visual requirements well, though permitting is a known constraint.",
      top_candidates: [
        {
          candidate: {
            name: "Windward Cliff Road",
            address_or_area: "Coastal Highway, marker 8",
            description:
              "A narrow cliffside road with dramatic ocean views, limited shoulder space.",
            evidence: [
              {
                source_url: "https://example.com/windward-cliff-road",
                source_title: "County road-use filming notice",
                snippet:
                  "Requires a traffic-control permit filed 15 business days in advance.",
              },
            ],
          },
          score: {
            visual_match: 85,
            feasibility: 70,
            logistics: 60,
            cost_fit: 55,
            permit_ease: 30,
            evidence_confidence: 60,
          },
          composite_score: 66.25,
        },
      ],
      conflicts: [
        {
          type: "permit",
          affected_scenes: [3],
          description:
            "Top candidate's permit ease score (30) falls below the acceptable threshold.",
          severity: "warning",
          suggested_resolution:
            "Begin the traffic-control permit application immediately if this candidate is chosen.",
        },
      ],
    },
    {
      scene_number: 4,
      location: "old railway station",
      recommended: "Coastal Junction Depot",
      rationale:
        "For this later scene, Coastal Junction Depot\u2019s coastal backdrop better matches the story beat, despite differing from scene 1\u2019s pick.",
      top_candidates: [
        {
          candidate: {
            name: "Coastal Junction Depot",
            address_or_area: "Coastal Line, Mile 12",
            description:
              "A smaller, less ornate depot with a coastal backdrop.",
            evidence: [],
          },
          score: {
            visual_match: 88,
            feasibility: 82,
            logistics: 75,
            cost_fit: 65,
            permit_ease: 80,
            evidence_confidence: 70,
          },
          composite_score: 79.4,
        },
      ],
      conflicts: [
        {
          type: "continuity",
          affected_scenes: [1, 4],
          description:
            "Scenes sharing location 'old railway station' have different top-ranked candidates: Coastal Junction Depot, Heritage Rail Platform.",
          severity: "warning",
          suggested_resolution:
            "Pick one candidate for all scenes at this location to preserve continuity.",
        },
      ],
    },
  ],
};
