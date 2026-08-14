# Components V2

Kairo uses Discord Components V2 for all interactive Discord interfaces,
built directly on **discord.py's native `discord.ui.LayoutView` system**.

There is no custom component abstraction — Kairo uses `discord.ui` types
directly and provides a small set of send helpers in `src/bot/components/`.

---

## What is Components V2?

Discord Components V2 is a message format where messages are built from
structured component objects (containers, sections, buttons, text) instead
of traditional embeds. It produces richer, more structured layouts.

discord.py 2.6+ provides full native support through `discord.ui.LayoutView`
and its associated component classes.

---

## Component Hierarchy

A Components V2 message uses a `LayoutView` as the top-level container:

```
LayoutView                     ← Passed as view= to send_message()
└── Container                  ← discord.ui.Container: top-level block
    ├── TextDisplay            ← discord.ui.TextDisplay: markdown text
    ├── Separator              ← discord.ui.Separator: spacing / divider
    ├── Section                ← discord.ui.Section: group + accessory
    │   ├── TextDisplay
    │   └── (accessory) Thumbnail / Button
    └── ActionRow              ← discord.ui.ActionRow: holds interactive items
        ├── Button             ← discord.ui.Button
        └── Select             ← discord.ui.Select (and variants)
```

A `LayoutView` can hold multiple top-level `Container` items.

---

## Quick Reference

```python
import discord
from src.bot.components import send_layout, edit_layout, followup_layout, send_layout_to_channel
```

All discord.ui CV2 types are also re-exported from `src.bot.components`:

```python
from src.bot.components import (
    LayoutView,
    Container,
    Section,
    TextDisplay,
    Separator,
    Thumbnail,
    ActionRow,
    Button,
    ButtonStyle,
    Select,
    Modal,
    TextInput,
    SeparatorSpacing,
    Paginator,
    send_layout,
    edit_layout,
    followup_layout,
    send_layout_to_channel,
)
```

---

## Sending a LayoutView

All CV2 messages are sent by passing a `LayoutView` as the `view=` argument.
The Kairo send helpers wrap this pattern and handle logging.

```python
import discord
from src.bot.components import send_layout

view = discord.ui.LayoutView()
view.add_item(discord.ui.Container(
    discord.ui.TextDisplay("Hello, world!"),
))

# Send as an interaction response
await send_layout(interaction, view, ephemeral=True)

# Edit the existing interaction response
await edit_layout(interaction, view)

# Send as a followup after deferring
await followup_layout(interaction, view, ephemeral=True)

# Send to a channel directly (not an interaction response)
message = await send_layout_to_channel(channel, view)
```

---

## LayoutView

`discord.ui.LayoutView` is the top-level class for CV2 messages.

```python
view = discord.ui.LayoutView()
view.add_item(discord.ui.Container(...))
view.add_item(discord.ui.Container(...))
await send_layout(interaction, view, ephemeral=True)
```

You can also subclass it and declare items as class attributes (useful for
static layouts or views with persistent button callbacks):

```python
class MyView(discord.ui.LayoutView):
    container = discord.ui.Container(
        discord.ui.TextDisplay("# Hello"),
    )
```

---

## Container

Top-level layout block. Can contain `TextDisplay`, `Separator`, `Section`,
`ActionRow`, and `MediaGallery` items. Optional accent colour bar on the left.

```python
discord.ui.Container(
    discord.ui.TextDisplay("Content goes here"),
    accent_colour=0x5865F2,   # Discord blurple — optional
)
```

Add items after construction:

```python
container = discord.ui.Container()
container.add_item(discord.ui.TextDisplay("Line 1"))
container.add_item(discord.ui.TextDisplay("Line 2"))
```

---

## TextDisplay

Renders markdown-formatted content. Supports all standard Discord markdown.

```python
discord.ui.TextDisplay("# Main Heading")
discord.ui.TextDisplay("**Bold**, *italic*, `code`, > blockquote")
discord.ui.TextDisplay("- Bullet\n- List")
```

---

## Separator

Adds visual spacing between components. The `visible` parameter controls
whether a visible horizontal line is rendered.

```python
discord.ui.Separator()                                           # Small space, no line
discord.ui.Separator(visible=True)                              # Visible divider line
discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large)
```

`spacing` accepts `discord.SeparatorSpacing.small` (default) or
`discord.SeparatorSpacing.large`.

---

## Section

Groups related `TextDisplay` items (up to 3) with a required **accessory**
component on the right side. The accessory is typically a `Thumbnail` or
a `Button`.

```python
discord.ui.Section(
    discord.ui.TextDisplay("## Alice"),
    discord.ui.TextDisplay("Joined 3 months ago"),
    accessory=discord.ui.Thumbnail(
        "https://cdn.discordapp.com/avatars/.../avatar.png",
        description="Alice's avatar",
    ),
)
```

> **Note:** `accessory=` is required — `Section` raises a `TypeError` if omitted.

---

## Thumbnail

Image component used as a `Section` accessory.

```python
discord.ui.Thumbnail(
    "https://example.com/image.png",
    description="Alt text for accessibility",
)
```

---

## Button

Clickable buttons. Must be placed inside an `ActionRow`.

```python
discord.ui.Button(
    label="Confirm",
    custom_id="action:confirm",
    style=discord.ButtonStyle.success,
)
discord.ui.Button(
    label="Cancel",
    custom_id="action:cancel",
    style=discord.ButtonStyle.danger,
)
discord.ui.Button(
    label="Learn More",
    style=discord.ButtonStyle.link,
    url="https://example.com",
)
```

Button styles:

| Style     | Colour | Use for                    |
|-----------|--------|----------------------------|
| `primary`   | Blue   | Main action                |
| `secondary` | Grey   | Secondary / neutral        |
| `success`   | Green  | Confirmation / positive    |
| `danger`    | Red    | Destructive / irreversible |
| `link`      | Grey   | Opens a URL (no custom_id) |

---

## ActionRow

Groups buttons (up to 5) or a single select menu. Must be inside a `Container`.

```python
discord.ui.ActionRow(
    discord.ui.Button(label="Yes", custom_id="confirm:yes", style=discord.ButtonStyle.success),
    discord.ui.Button(label="No",  custom_id="confirm:no",  style=discord.ButtonStyle.danger),
)
```

---

## Select Menus

discord.py provides multiple select variants:

```python
# String options select
discord.ui.Select(
    custom_id="config:feature",
    placeholder="Select a feature...",
    options=[
        discord.SelectOption(label="Moderation", value="moderation", emoji="🔨"),
        discord.SelectOption(label="AutoMod",    value="automod",    emoji="🤖"),
    ],
    min_values=1,
    max_values=1,
)

# Other variants
discord.ui.UserSelect(custom_id="select:user")
discord.ui.RoleSelect(custom_id="select:role")
discord.ui.ChannelSelect(custom_id="select:channel")
discord.ui.MentionableSelect(custom_id="select:mentionable")
```

---

## Modal

Pop-up form for collecting text input. Sent as an interaction response.

```python
class ReportModal(discord.ui.Modal, title="Report a User"):
    reason = discord.ui.TextInput(
        label="Reason",
        placeholder="Describe the issue...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"Report received: {self.reason.value}",
            ephemeral=True,
        )

# Send the modal from a slash command or button handler:
await interaction.response.send_modal(ReportModal())
```

---

## Paginator

Kairo's `Paginator` is a `LayoutView` subclass with Previous / Next buttons.
Each page is a `discord.ui.Container`.

```python
from src.bot.components import Paginator

pages = [
    discord.ui.Container(discord.ui.TextDisplay(f"Page {i + 1} content"))
    for i in range(5)
]

view = Paginator(pages, ephemeral=True)
await interaction.response.send_message(view=view, ephemeral=True)
```

The paginator handles the button interactions internally — no extra setup needed.

---

## Complete Example

A user-info panel using Section with Thumbnail and a Separator:

```python
import discord
from src.bot.components import send_layout

async def show_userinfo(interaction: discord.Interaction, member: discord.Member) -> None:
    created = discord.utils.format_dt(member.created_at, "R")
    joined  = discord.utils.format_dt(member.joined_at, "R") if member.joined_at else "Unknown"

    view = discord.ui.LayoutView()
    view.add_item(discord.ui.Container(
        discord.ui.Section(
            discord.ui.TextDisplay(f"## {member.display_name}"),
            discord.ui.TextDisplay(f"`{member}` • {member.mention}"),
            accessory=discord.ui.Thumbnail(
                member.display_avatar.url,
                description=f"{member.display_name}'s avatar",
            ),
        ),
        discord.ui.Separator(visible=True),
        discord.ui.TextDisplay(
            f"**ID:** `{member.id}`\n"
            f"**Account created:** {created}\n"
            f"**Joined server:** {joined}\n"
            f"**Top role:** {member.top_role.mention}"
        ),
    ))

    await send_layout(interaction, view, ephemeral=True)
```

---

## Notes for Developers

- CV2 messages are sent via `view=` — **not** `components=`. Passing `components=` directly is not supported by discord.py.
- `Section.accessory` is **required** — omitting it raises `TypeError`.
- `Separator` uses `visible=` to control the divider line, not `divider=`.
- `Button` requires `custom_id=` for all non-link styles; link buttons require `url=` instead.
- A single `LayoutView` can hold up to 40 total items across all nested components.
- `TextDisplay` content counts toward a 4000-character limit across the whole view.
- See the [Discord API docs](https://discord.com/developers/docs/components/overview) for the full CV2 spec.
