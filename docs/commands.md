# Commands

Kairo provides a comprehensive set of slash commands organized by feature category.

---

## 🔨 Moderation Commands

All moderation commands require appropriate Discord permissions. Users with Administrator, Manage Guild, or the configured Moderator Role can use these commands.

| Command | Description | Usage |
|---------|-------------|-------|
| `/ban` | Ban a member from the server | `/ban @user [reason] [delete_days]` |
| `/kick` | Kick a member from the server | `/kick @user [reason]` |
| `/timeout` | Temporarily mute a member | `/timeout @user 10m [reason]` |
| `/warn` | Issue a warning to a member | `/warn @user [reason]` |
| `/history` | View a member's moderation history | `/history @user` |
| `/case` | View a specific moderation case | `/case 42` |

### Time Format for Timeout
Supports the following time units:
- `10s` - 10 seconds
- `5m` - 5 minutes  
- `1h` - 1 hour
- `1d` - 1 day
- `1w` - 1 week

Examples: `/timeout @user 30m`, `/timeout @user 2h Spam in general`

### Moderation Features
- All actions create moderation cases with unique IDs
- Cases are logged to the configured mod-log channel with rich Components V2 formatting
- Warning history is tracked per user
- Cases can be viewed individually or as a user's complete history

---

## 🤖 AutoMod Commands

AutoMod commands require administrator permissions.

| Command | Description | Usage |
|---------|-------------|-------|
| `/automod` | Configure AutoMod settings | `/automod` |

> **Note:** Most AutoMod configuration is done through the configuration system. AutoMod automatically monitors messages and member joins based on configured rules. Full rule engine is implemented in Phase 3 with spam detection, mention spam, link filtering, word filtering, caps filtering, and raid protection.

### AutoMod Rule Types
- **Spam Detection**: Too many messages in a time window
- **Mention Spam**: Too many @mentions in a single message
- **Link Filtering**: Block Discord invites, external URLs, or specific domains
- **Word Filtering**: Block specific words or phrases
- **Caps Filtering**: Detect excessive capitalization
- **Raid Protection**: Detect rapid mass joins

### Configurable Actions
When a rule is triggered, AutoMod can:
- Warn the user
- Timeout the user
- Kick the user
- Ban the user
- Delete the message
- Notify moderators

---

## 🎉 Welcome & Leave Commands

Welcome and leave message configuration. All commands require administrator permissions.

| Command | Description | Usage |
|---------|-------------|-------|
| `/welcome set` | Set welcome channel and message | `/welcome set #welcome Welcome {member}!` |
| `/welcome leave` | Configure leave messages | `/welcome leave #goodbye {member} left` |
| `/welcome disable` | Disable welcome messages | `/welcome disable` |

### Template Variables
Welcome and leave messages support the following template variables:
- `{member}` - Member's username
- `{server}` - Server name
- `{count}` - Server member count
- `{mention}` - Member mention (e.g., @Username)
- `{user}` - Member's full username with discriminator

Example: `Welcome {member} to {server}! You are member #{count}`

### Auto-Role Configuration
| Command | Description | Usage |
|---------|-------------|-------|
| `/autorole set` | Set the role to auto-assign to new members | `/autorole set @Member` |
| `/autorole clear` | Clear the auto-role | `/autorole clear` |

---

## 🎭 Role Commands

All role commands require `Manage Roles` permission.

| Command | Description | Usage |
|---------|-------------|-------|
| `/role_button` | Create a button that assigns a role | `/role_button @Role [label] [emoji] [description]` |
| `/role_menu` | Create a select menu with multiple roles | `/role_menu "@Role1,@Role2" [title] [description] [placeholder] [max_values]` |
| `/role_panel` | Create a panel with multiple role buttons | `/role_panel [title] [description]` |
| `/addrole` | Manually add a role to a member | `/addrole @member @role [reason]` |
| `/removerole` | Manually remove a role from a member | `/removerole @member @role [reason]` |

### Role Button Features
- Click to get the role, click again to remove (toggle behavior)
- Supports custom labels and emojis
- Can include a description above the button
- Uses Discord Components V2 for rich formatting

### Role Menu Options
- `roles`: Comma-separated list of @role mentions (required)
- `title`: Menu title displayed above the select menu
- `description`: Descriptive text shown below the title
- `placeholder`: Text shown when no selection is made
- `max_values`: Maximum number of roles a user can select (1-25)

### Role Panel Features
- Opens a modal for easy configuration
- Creates multiple role buttons in a single message
- Buttons are arranged in rows (up to 5 per row)
- Each button can be clicked to toggle the corresponding role

---

## ⚙️ Configuration Commands

All configuration commands require administrator permissions. These commands manage server-specific Kairo settings.

| Command | Description | Usage |
|---------|-------------|-------|
| `/setup` | Initial server setup with configuration status | `/setup` |
| `/set_modlog` | Set the moderation logging channel | `/set_modlog #mod-log` |
| `/set_locale` | Set the server language locale | `/set_locale en` |
| `/set_modrole` | Set the role that grants moderator access | `/set_modrole @Moderator` |
| `/config_show` | Display current server configuration | `/config_show` |
| `/config_reset` | Reset configuration to defaults | `/config_reset` |
| `/toggle_welcome` | Enable/disable welcome messages | `/toggle_welcome true` |
| `/toggle_leave` | Enable/disable leave messages | `/toggle_leave true` |

### Configuration System Features
- Centralized server configuration stored in SQLite database
- Per-guild settings for all features
- Feature toggles for welcome/leave messages
- Channel configuration for mod-log, log, welcome, and leave channels
- Role configuration for moderator role and auto-role
- Locale/language settings

---

## 📋 Logging Commands

Logging commands are currently in development. Guild join/remove events, message edits, and message deletions are tracked in the database and will be displayed through the logging system.

---

## 🔧 Utility Commands

General purpose commands available to all users.

| Command | Description | Usage |
|---------|-------------|-------|
| `/help` | Show available commands grouped by category | `/help` |
| `/ping` | Check bot latency | `/ping` |
| `/botinfo` | Display information about Kairo | `/botinfo` |
| `/userinfo` | Display information about a user | `/userinfo [@user]` |
| `/serverinfo` | Display information about the server | `/serverinfo` |
| `/avatar` | Display a user's avatar | `/avatar [@user]` |

### Help Command Features
- Displays commands organized by category
- Shows command descriptions
- Uses Components V2 for rich formatting

---

## Command Permissions

| Permission | Commands |
|------------|----------|
| Administrator | `/setup`, `/set_*`, `/config_*`, `/toggle_*`, `/autorole`, `/welcome`, `/automod` |
| Manage Roles | `/role_button`, `/role_menu`, `/role_panel`, `/addrole`, `/removerole` |
| Moderator Role or Admin | `/ban`, `/kick`, `/timeout`, `/warn`, `/history`, `/case` |
| Everyone | `/help`, `/ping`, `/botinfo`, `/userinfo`, `/serverinfo`, `/avatar` |

---

## Command Categories in `/help`

The `/help` command displays commands grouped by these categories:

- **🔧 Utility** - General purpose commands
- **🔨 Moderation** - Moderation actions and history
- **🤖 AutoMod** - AutoMod configuration
- **🎉 Welcome** - Welcome and leave message configuration
- **🎭 Roles** - Role assignment commands
- **⚙️ Config** - Server configuration commands

---

## Command Availability

Some commands may not be available if:

1. **The feature is disabled** in the server configuration
2. **The bot lacks permissions** to perform the action
3. **The user lacks permissions** to use the command
4. **The command is guild-only** but used in DMs

When a command is unavailable, Kairo will typically respond with an appropriate error message explaining the reason.

---

## Phase 3 Implementation Notes

All commands listed above are fully implemented in Phase 3, including:
- Complete moderation system with case tracking
- Full AutoMod rule engine
- Welcome/leave messages with template variables
- Auto-role assignment
- Role buttons, menus, and panels
- Centralized server configuration
- All utility commands

Future phases will add additional features like tickets, giveaways, leveling, and more.