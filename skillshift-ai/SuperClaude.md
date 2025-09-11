⏺ Auto-Activation vs Manual Control

🤖 Automatic Activation

Personas auto-activate based on multi-factor scoring:

- Keyword Matching (30%): Domain-specific terms
- Context Analysis (40%): Project phase, complexity, urgency
- User History (20%): Past preferences and successful
  outcomes
- Performance Metrics (10%): Current system state

Auto-Activation Examples:
"create React component" → --persona-frontend + --magic
"API authentication issue" → --persona-backend +
--persona-security
"performance bottleneck" → --persona-performance +
--think-hard
"debug complex system" → --persona-analyzer + --seq

🎛️ Manual Override

Force specific personas with explicit flags:
--persona-architect # Systems design specialist
--persona-frontend # UX/UI specialist  
 --persona-backend # API/server specialist
--persona-security # Security expert
--persona-performance # Optimization specialist
--persona-analyzer # Investigation expert
--persona-qa # Quality assurance
--persona-refactorer # Code quality specialist
--persona-devops # Infrastructure specialist
--persona-mentor # Educational guidance
--persona-scribe=lang # Documentation specialist

🏗️ Architect - Systems Design Specialist

Priority: Long-term maintainability > scalability >
performance

Use Cases:

- System architecture planning
- Database schema design
- API design patterns
- Technical debt assessment

Example Commands:
/analyze "evaluate our microservices architecture"
/design system --persona-architect
/estimate "migrating to event-driven architecture"

🎨 Frontend - UX/UI Specialist

Priority: User needs > accessibility > performance

Use Cases:

- React/Vue component development
- Responsive design implementation
- Accessibility compliance
- Performance optimization

Example Commands:
/implement dashboard component --persona-frontend
/improve --focus accessibility --persona-frontend
/build --type ui --persona-frontend

⚙️ Backend - API/Server Specialist

Priority: Reliability > security > performance

Use Cases:

- REST/GraphQL API development
- Database optimization
- Server-side logic
- Data integrity validation

Example Commands:
/implement user authentication API --persona-backend
/troubleshoot database performance --persona-backend
/analyze API bottlenecks --persona-backend

🛡️ Security - Threat Modeling Expert

Priority: Security > compliance > reliability

Use Cases:

- Vulnerability assessment
- Authentication/authorization
- Security code review
- Compliance validation

Example Commands:
/analyze --focus security --persona-security
/implement OAuth2 flow --persona-security
/audit authentication system --persona-security

⚡ Performance - Optimization Specialist

Priority: Measure first > optimize critical path > user
experience

Use Cases:

- Performance profiling
- Bottleneck identification
- Code optimization
- Resource usage analysis

Example Commands:
/analyze performance bottlenecks --persona-performance
/improve --focus performance --persona-performance
/benchmark application performance --persona-performance

🔍 Analyzer - Investigation Expert

Priority: Evidence > systematic approach > thoroughness

Use Cases:

- Root cause analysis
- Bug investigation
- System diagnostics
- Pattern recognition

Example Commands:
/troubleshoot production issues --persona-analyzer
/analyze error patterns --persona-analyzer
/investigate system failures --persona-analyzer

✅ QA - Quality Assurance Specialist

Priority: Prevention > detection > correction

Use Cases:

- Test strategy development
- Quality gate implementation
- Edge case identification
- Testing automation

Example Commands:
/test comprehensive --persona-qa
/analyze quality metrics --persona-qa
/implement testing strategy --persona-qa

🔧 Refactorer - Code Quality Specialist

Priority: Simplicity > maintainability > readability

Use Cases:

- Code cleanup
- Technical debt reduction
- Pattern standardization
- Maintainability improvement

Example Commands:
/cleanup legacy code --persona-refactorer
/improve code quality --persona-refactorer
/refactor component structure --persona-refactorer

🚀 DevOps - Infrastructure Specialist

Priority: Automation > observability > reliability

Use Cases:

- CI/CD pipeline setup
- Infrastructure automation
- Monitoring implementation
- Deployment optimization

Example Commands:
/implement CI/CD pipeline --persona-devops
/setup monitoring --persona-devops
/optimize deployment process --persona-devops

🎓 Mentor - Educational Guide

Priority: Understanding > knowledge transfer > teaching

Use Cases:

- Technical explanations
- Learning path guidance
- Best practice education
- Knowledge documentation

Example Commands:
/explain React hooks --persona-mentor
/document API patterns --persona-mentor
/guide junior developer --persona-mentor

📝 Scribe - Documentation Specialist

Priority: Clarity > audience needs > cultural sensitivity

Use Cases:

- Technical documentation
- API documentation
- User guides
- Multilingual content

Example Commands:
/document API endpoints --persona-scribe=en
/write user manual --persona-scribe=es
/create technical guide --persona-scribe=fr

⏺ Integration with Commands, Flags & MCP Servers

🎯 Command Integration

Personas automatically optimize these commands:

Development Commands:

- /build → architect, frontend, backend (based on context)
- /implement → domain-specific persona + MCP servers
- /design → architect + frontend collaboration

Analysis Commands:

- /analyze → analyzer + domain expert
- /troubleshoot → analyzer + relevant specialist
- /explain → mentor + domain expert

Quality Commands:

- /improve → refactorer + performance + security
- /cleanup → refactorer + architect
- /test → qa + relevant domain expert

🏢 MCP Server Preferences

Each persona has optimized MCP server preferences:

Context7 (Documentation):

- architect, backend, devops, scribe
- Best for: Patterns, frameworks, official docs

Sequential (Complex Analysis):

- analyzer, architect, security, performance
- Best for: Multi-step reasoning, systematic analysis

Magic (UI Components):

- frontend, refactorer (for UI cleanup)
- Best for: React/Vue components, design systems

Playwright (Testing):

- qa, frontend, performance
- Best for: E2E testing, user workflows

🔧 Flag Combinations

Effective Persona + Flag Combinations:

# Security-focused analysis

--persona-security --focus security --validate --seq

# Performance optimization

--persona-performance --focus performance --think-hard --play

# UI development

--persona-frontend --magic --c7 --focus accessibility

# System architecture

--persona-architect --think-hard --seq --c7

# Code quality improvement

--persona-refactorer --loop --validate --seq

# Documentation creation

--persona-scribe=en --c7 --focus documentation

---

⏺ Update Todos
⎿ ☒ Create SuperClaude Persona system overview and core  
 concepts
☒ Document persona auto-activation patterns and manual
override methods
☒ Provide practical examples and use cases for each
persona type
☒ Explain persona integration with commands, flags, and
MCP servers

⏺ Practical Usage Scenarios

🎯 Project Context: Your MLBB AI Coach

Based on your skillshift-ai project, here are practical persona applications:

Frontend Development:

# Creating dashboard components

/implement performance analytics dashboard --persona-frontend

# Improving UI accessibility

/improve --focus accessibility --persona-frontend

Backend ML/AI Work:

# Optimizing YOLO detection

/analyze hero detection accuracy --persona-performance

# Implementing new ML models

/implement team synergy analyzer --persona-backend

System Architecture:

# Evaluating current architecture

/analyze system architecture --persona-architect

# Planning scalability improvements

/design microservices migration --persona-architect

Security & Quality:

# Security audit

/analyze --focus security --persona-security

# Code quality improvement

/improve --focus quality --persona-refactorer --loop

🤝 Cross-Persona Collaboration

Personas automatically collaborate when needed:

Frontend + Security:
/implement user authentication UI --persona-frontend

# Auto-activates security persona for auth logic

Backend + Performance:
/analyze API response times --persona-backend

# Auto-activates performance persona for optimization

Architect + Multiple Specialists:
/design complete system overhaul --persona-architect

# Auto-activates relevant specialists based on components

📊 Best Practices

1. Start with Auto-Activation: Let the system choose personas based on context
2. Use Manual Override: When you need specific expertise
3. Combine with Flags: Enhance persona effectiveness with appropriate flags
4. Monitor Results: Pay attention to which personas produce best results for your use cases
5. Learn Patterns: Understand which persona combinations work best for your project types

🚀 Quick Reference

For Your ML/AI Project:

- YOLO model work: --persona-performance or --persona-backend
- Dashboard UI: --persona-frontend
- System optimization: --persona-architect
- Code cleanup: --persona-refactorer
- Documentation: --persona-scribe=en
- Testing: --persona-qa
- Debugging: --persona-analyzer

The persona system adapts to your specific needs and learns from successful interactions, making
it increasingly effective for your development workflows.
