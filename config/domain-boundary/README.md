# Domain Boundary Policy Profiles

Place project-specific JSON profiles here and select one with:

    domain_boundary_audit {"policy_profile":"<name>"}

JSON profiles are gitignored local sidecar state. They remain detachable from the project and are
preserved across update installs. Each profile uses the same shape as the inline policy argument:

    {
      "name": "Example application-service architecture",
      "layers": {"cli": "adapter", "services": "application", "domain": "domain"},
      "allowed_edges": ["adapter->application", "application->domain"]
    }

Same-layer imports are allowed. Mapped layer edges not listed in allowed_edges are violations.
Unmapped domains are reported and treated as distinct strict layers so new packages cannot pass
silently. Profile names accept letters, digits, hyphens, and underscores only.
