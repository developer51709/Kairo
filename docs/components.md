# Components V2

Kairo uses Discord Components V2 for all interactive Discord interfaces.
Rather than constructing raw component dicts everywhere, Kairo provides a
clean abstraction layer in `src/bot/components/`.

---

## What is Components V2?

Discord Components V2 is a message format where messages are built from
structured component objects (containers, sections, buttons, text) instead
of traditional embeds. It produces richer, more structured layouts.

Components V2 requires the `IS_COMPONENTS_V2` message flag (`1 << 15`) and
is only available for bot accounts with the appropriate access.

---

## Component Hierarchy

A Components V2 message is structured as:

```
Panel                          ← Kairo: owns all containers; handles sending
└── Container                  ← Discord type 17: top-level block
    ├── Text                   ← Discord type 10: markdown text
    ├── Separator              ← Discord type 14: visual spacing / divider
    ├── Section                ← Discord type 9: group with optional thumbnail
    │   └── Text
    └── ActionRow              ← Discord type 1: holds interactive components
        ├── Button             ← Discord type 2
        └── SelectMenu         ← Discord type 3
```

A message can have multiple Containers inside one Panel.

---

## Quick Reference

```python
from src.bot.components import (
    Panel, Container, Section,
    Text, Separator,
    Button, ButtonStyle, SelectMenu, SelectOption, ActionRow,
    Modal, TextInput, TextInputStyle,
    Paginator,
)
```

---

## Panel

`Panel` is the main entry point. It wraps one or more `Container` objects
and handles sending to Discord.

```python
panel = Panel(
    Container(
        Text("Hello world!"),
    )
)

# Send as an interaction response
await panel.send(interaction)

# Edit the existing interaction response
await panel.edit(interaction)

# Send as a followup after deferring
await panel.followup(interaction)

# Send to a channel directly (not as interaction response)
message = await panel.send_to_channel(channel)
```

**Ephemeral panels** (visible only to the invoking user):

```python
panel = Panel(Container(Text("Only you can see this.")), ephemeral=True)
await panel.send(interaction)
```

---

## Container

Top-level component block. Can have an optional left-side accent colour.

```python
Container(
    Text("Content goes here"),
    accent_colour=0x5865F2,   # Discord blurple
)
```

Add components after construction:

```python
container = Container()
container.add(Text("Line 1"), Text("Line 2"))
```

---

## Section

Groups content with an optional right-side thumbnail image.

```python
Section(
    Text("## Alice"),
    Text("Joined 3 months ago"),
    thumbnail_url="https://cdn.discordapp.com/avatars/.../avatar.png",
    thumbnail_alt="Alice's avatar",
)
```

---

## Text

Renders markdown-formatted content. Supports all standard Discord markdown.

```python
Text("# Main Heading")
Text("**Bold**, *italic*, `code`, > blockquote")
Text("- Bullet\n- List")
```

---

## Separator

Adds visual spacing between components.

```python
Separator()                              # Small space
Separator(divider=True)                  # Visible horizontal line
Separator(divider=True, spacing="large") # Line with more space
```

---

## Button

Clickable buttons that trigger interactions.

```python
Button(label="Confirm", custom_id="action:confirm", style=ButtonStyle.SUCCESS)
Button(label="Cancel", custom_id="action:cancel", style=ButtonStyle.DANGER)
Button(label="Learn More", style=ButtonStyle.LINK, url="https://example.com")
Button(label="Disabled", custom_id="action:x", disabled=True)
```

Button styles:

| Style       | Colour | Use for                          |
|-------------|--------|----------------------------------|
| `PRIMARY`   | Blue   | Main action                      |
| `SECONDARY` | Grey   | Secondary / neutral              |
| `SUCCESS`   | Green  | Confirmation / positive          |
| `DANGER`    | Red    | Destructive / irreversible       |
| `LINK`      | Grey   | Link to external URL             |

---

## SelectMenu

Dropdown menu with selectable options.

```python
SelectMenu(
    custom_id="config:feature",
    placeholder="Select a feature...",
    options=[
        SelectOption(label="Moderation", value="moderation", emoji="🔨"),
        SelectOption(label="AutoMod", value="automod", emoji="🤖"),
        SelectOption(label="Logging", value="logging", emoji="📋"),
    ],
    min_values=1,
    max_values=1,
)
```

---

## ActionRow

Groups buttons or a select menu. Required wrapper for interactive components.

```python
# Buttons (up to 5 per row)
ActionRow(
    Button(label="Yes", custom_id="confirm:yes", style=ButtonStyle.SUCCESS),
    Button(label="No", custom_id="confirm:no", style=ButtonStyle.DANGER),
)

# Select menu (one per row)
ActionRow(
    SelectMenu(custom_id="select:role", options=[...])
)
```

---

## Modal

Pop-up form for collecting text input. Sent as an interaction response
(not as a message — must be the first response to an interaction).

```python
modal = Modal(
    title="Report a User",
    custom_id="report:submit",
    inputs=[
        TextInput(
            label="Reason",
            custom_id="report:reason",
            placeholder="Describe the issue...",
            style=TextInputStyle.PARAGRAPH,
            required=True,
            max_length=1000,
        ),
    ],
)
await interaction.response.send_modal(modal.to_discord_modal())
```

---

## Paginator

Multi-page interface for long lists.

```python
async def build_page(items, page_num, total_pages):
    return [
        Text(f"## Results — Page {page_num + 1}/{total_pages}"),
        Separator(divider=True),
        *[Text(f"• {item}") for item in items],
    ]

paginator = Paginator(
    items=all_results,
    page_size=10,
    build_page=build_page,
    custom_id_prefix="results",
)
await paginator.send(interaction)
```

To handle navigation button interactions, update the paginator and re-send:

```python
@bot.event
async def on_interaction(interaction):
    custom_id = interaction.data.get("custom_id", "")
    if custom_id == "results:next":
        paginator.next_page()
        container = await paginator.build_container()
        await Panel(container).edit(interaction)
    elif custom_id == "results:prev":
        paginator.prev_page()
        container = await paginator.build_container()
        await Panel(container).edit(interaction)
```

---

## Complete Example

A moderation history panel with sections and navigation buttons:

```python
from src.bot.components import (
    Panel, Container, Section, Text, Separator,
    Button, ButtonStyle, ActionRow,
)

async def show_user_panel(interaction, member, cases):
    panel = Panel(
        Container(
            Section(
                Text(f"## Moderation History"),
                Text(f"**User:** {member.mention}\n**Cases:** {len(cases)}"),
                thumbnail_url=member.display_avatar.url,
                thumbnail_alt=f"{member.display_name}'s avatar",
            ),
            Separator(divider=True),
            *[
                Text(
                    f"**Case #{c.id}** — {c.case_type.value}\n"
                    f"Reason: {c.reason or 'None'}"
                )
                for c in cases[:5]
            ],
            Separator(),
            ActionRow(
                Button(
                    label="View All Cases",
                    custom_id=f"history:all:{member.id}",
                    style=ButtonStyle.SECONDARY,
                ),
            ),
        ),
        ephemeral=True,
    )
    await panel.send(interaction)
```

---

## Notes for Developers

- Components V2 messages cannot mix components and content/embeds in the same message.
- The `IS_COMPONENTS_V2` flag is set automatically by `Panel.send()` — you do not need to set it manually.
- Buttons with `disabled=True` are visible but unclickable — use this for the current-page indicator in paginators.
- `custom_id` values must be unique within a message and max 100 characters.
- See the [Discord API docs](https://discord.com/developers/docs/interactions/message-components) for full spec.
