from asyncio import TimeoutError
from time import time
from typing import List, Optional, Union
from random import randint

from discord import Embed, Emoji, Member, PartialEmoji, Role, TextChannel, User
from discord.abc import User as userUser
from discord.ext.commands import AutoShardedBot, Bot, Context
from discord.role import Role as roleRole
from discord_slash.context import ComponentContext, InteractionContext
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import (
    create_actionrow,
    create_button,
    create_select,
    create_select_option,
    wait_for_component,
)

from .errors import (
    BadButtons,
    BadOnly,
    IncorrectDataType,
    TooManyButtons,
)


class TimedOut:
    def __init__(
        self,
        ctx,
        buttonContext,
        timeTaken,
        lastContent,
        lastEmbed,
        successfulUsers,
        failedUsers,
    ):
        self.ctx = ctx
        self.buttonContext = buttonContext
        self.timeTaken = timeTaken
        self.lastContent = lastContent
        self.lastEmbed = lastEmbed
        self.successfulUsers = successfulUsers
        self.failedUsers = failedUsers


class Paginator:
    def __init__(
        self,
        bot: Union[AutoShardedBot, Bot],
        ctx: Union[
            InteractionContext,
            Context,
            TextChannel,
            User,
            Member,
        ],
        pages: List[Embed],
        content: Optional[Union[str, List[str]]] = None,
        hidden: Optional[bool] = False,
        authorOnly: Optional[bool] = False,
        onlyFor: Optional[
            Union[
                User,
                Role,
                List[Union[User, Role]],
            ]
        ] = None,
        dm: Optional[bool] = False,
        useOverflow: Optional[bool] = True,
        timeout: Optional[int] = None,
        disableAfterTimeout: Optional[bool] = True,
        deleteAfterTimeout: Optional[bool] = False,
        useSelect: Optional[bool] = True,
        useButtons: Optional[bool] = True,
        useIndexButton: Optional[bool] = None,
        useLinkButton: Optional[bool] = False,
        useFirstLast: Optional[bool] = True,
        firstLabel: Optional[str] = "",
        prevLabel: Optional[str] = "",
        indexLabel: Optional[str] = "Page",
        nextLabel: Optional[str] = "",
        lastLabel: Optional[str] = "",
        linkLabel: Optional[Union[str, List[str]]] = "",
        linkURL: Optional[Union[str, List[str]]] = "",
        customButtonLabel: Optional[str] = None,
        firstEmoji: Optional[Union[Emoji, PartialEmoji, dict, str]] = "⏮️",
        prevEmoji: Optional[Union[Emoji, PartialEmoji, dict, str]] = "◀",
        nextEmoji: Optional[Union[Emoji, PartialEmoji, dict, str]] = "▶",
        lastEmoji: Optional[Union[Emoji, PartialEmoji, dict, str]] = "⏭️",
        customButtonEmoji: Optional[Union[Emoji, PartialEmoji, dict, str]] = None,
        firstStyle: Optional[Union[ButtonStyle, int]] = 1,
        prevStyle: Optional[Union[ButtonStyle, int]] = 1,
        indexStyle: Optional[Union[ButtonStyle, int]] = 2,
        nextStyle: Optional[Union[ButtonStyle, int]] = 1,
        lastStyle: Optional[Union[ButtonStyle, int]] = 1,
        customButtonStyle: Optional[Union[ButtonStyle, int]] = 2,
    ) -> TimedOut:
        self.bot = bot
        self.ctx = ctx
        self.pages = pages
        self.content = content
        self.hidden = hidden
        self.authorOnly = authorOnly
        self.onlyFor = onlyFor
        self.dm = dm
        self.useOverflow = useOverflow
        self.timeout = timeout
        self.disableAfterTimeout = disableAfterTimeout
        self.deleteAfterTimeout = deleteAfterTimeout
        self.useSelect = useSelect
        self.useButtons = useButtons
        self.useIndexButton = useIndexButton
        self.useLinkButton = useLinkButton
        self.useFirstLast = useFirstLast
        self.labels = [firstLabel, prevLabel, indexLabel, nextLabel, lastLabel]
        self.links = [linkLabel, linkURL]
        self.customButtonLabel = customButtonLabel
        self.emojis = [firstEmoji, prevEmoji, nextEmoji, lastEmoji]
        self.customButtonEmoji = customButtonEmoji
        self.styles = [firstStyle, prevStyle, indexStyle, nextStyle, lastStyle]
        self.customButtonStyle = customButtonStyle

        self.top = len(self.pages)  # limit of the paginator
        self.multiContent = False
        self.multiLabel = False
        self.multiURL = False
        self.useCustomButton = False
        try:
            self.successfulUsers = [ctx.author]
        except AttributeError:
            self.successfulUsers = [ctx]
        self.failedUsers = []

        self.index = 1
        self.random_id = randint(1, 999999)

        # ERROR HANDLING

        self.incdata(
            "bot",
            self.bot,
            (AutoShardedBot, Bot),
            "commands.Bot or commands.AutoShardedBot",
        )
        self.incdata(
            "ctx",
            self.ctx,
            (InteractionContext, Context, TextChannel, User, Member),
            "InteractionContext, commands.Context, discord.TextChannel, discord.User, or discord.Member",
        )
        self.incdata(
            "content", self.content, (list, str, type(None)), "str or list(str)"
        )
        self.incdata("hidden", self.hidden, bool, "bool")
        self.incdata("authorOnly", self.authorOnly, bool, "bool")
        self.incdata(
            "onlyFor",
            self.onlyFor,
            (User, Role, list, type(None)),
            "discord.User/Role, or list(discord.User/Role)",
        )
        self.incdata("dm", self.dm, bool, "bool")
        self.incdata("useOverflow", self.useOverflow, bool, "bool")
        self.incdata("timeout", self.timeout, (int, type(None)), "int")
        bools = {
            "disableAfterTimeout": self.disableAfterTimeout,
            "deleteAfterTimeout": self.deleteAfterTimeout,
            "useSelect": self.useSelect,
            "useLinkButton": self.useLinkButton,
        }
        for b in bools:
            self.incdata(
                b,
                bools[b],
                bool,
                "bool",
            )
        self.incdata("useIndexButton", self.useIndexButton, (bool, type(None)), "bool")
        labels = {
            "firstLabel": firstLabel,
            "prevLabel": prevLabel,
            "indexLabel": indexLabel,
            "nextLabel": nextLabel,
            "lastLabel": lastLabel,
            "linkLabel": linkLabel,
            "linkURL": linkURL,
        }
        for label in labels:
            self.incdata(
                label,
                labels[label],
                str,
                "str",
            )
        self.incdata(
            "customButtonLabel", self.customButtonLabel, (str, type(None)), "str"
        )
        emojis = {
            "firstEmoji": firstEmoji,
            "prevEmoji": prevEmoji,
            "nextEmoji": nextEmoji,
            "lastEmoji": lastEmoji,
        }
        for emoji in emojis:
            self.incdata(
                emoji,
                emojis[emoji],
                (Emoji, PartialEmoji, dict, str),
                "Emoji, PartialEmoji, dict, or str",
            )
        styles = {
            "firstStyle": firstStyle,
            "prevStyle": prevStyle,
            "indexStyle": indexStyle,
            "nextStyle": nextStyle,
            "lastStyle": lastStyle,
        }
        for style in styles:
            self.incdata(
                style,
                styles[style],
                (ButtonStyle, int),
                "ButtonStyle or int",
            )
        if self.useIndexButton and not self.useButtons:
            BadButtons("Index button cannot be used with useButtons=False!")
            self.useIndexButton = False

        if self.authorOnly and self.onlyFor:
            BadOnly()
            self.authorOnly = False

        if self.customButtonLabel is not None:
            self.useCustomButton = True

        if self.useSelect and len(self.pages) > 25:
            self.useSelect = False
            if self.useIndexButton is None:
                self.useIndexButton = True

    async def run(self) -> TimedOut:
        try:
            if self.dm:
                if isinstance(self.ctx, InteractionContext) or isinstance(
                    self.ctx, Context
                ):
                    msg = await self.ctx.author.send(
                        content=self.content[0] if self.multiContent else self.content,
                        embed=self.pages[0],
                        components=list(
                            filter(
                                None,
                                [
                                    self.select_row() if self.useSelect else None,
                                    self.buttons_row() if self.useButtons else None,
                                    self.overflow_row() if self.useOverflow else None,
                                ],
                            )
                        ),
                        hidden=self.hidden,
                    )
                    await self.ctx.send("Check your DMs!", hidden=True)
                elif isinstance(self.ctx, userUser):
                    msg = await self.ctx.send(
                        content=self.content[0] if self.multiContent else self.content,
                        embed=self.pages[0],
                        components=list(
                            filter(
                                None,
                                [
                                    self.select_row() if self.useSelect else None,
                                    self.buttons_row() if self.useButtons else None,
                                    self.overflow_row() if self.useOverflow else None,
                                ],
                            )
                        ),
                        hidden=self.hidden,
                    )
                else:
                    IncorrectDataType(
                        "ctx",
                        "InteractionContext or commands.Context for dm=True",
                        self.ctx,
                    )
            else:
                msg = await self.ctx.send(
                    content=self.content[0] if self.multiContent else self.content,
                    embed=self.pages[0],
                    components=list(
                        filter(
                            None,
                            [
                                self.select_row() if self.useSelect else None,
                                self.buttons_row() if self.useButtons else None,
                                self.overflow_row() if self.useOverflow else None,
                            ],
                        )
                    ),
                    hidden=self.hidden,
                )
        except TypeError:
            if self.dm:
                if isinstance(self.ctx, InteractionContext) or isinstance(
                    self.ctx, Context
                ):
                    msg = await self.ctx.author.send(
                        content=self.content[0] if self.multiContent else self.content,
                        embed=self.pages[0],
                        components=list(
                            filter(
                                None,
                                [
                                    self.select_row() if self.useSelect else None,
                                    self.buttons_row() if self.useButtons else None,
                                    self.overflow_row() if self.useOverflow else None,
                                ],
                            )
                        ),
                    )
                    await self.ctx.send("Check your DMs!", hidden=True)
                elif isinstance(self.ctx, userUser):
                    msg = await self.ctx.send(
                        content=self.content[0] if self.multiContent else self.content,
                        embed=self.pages[0],
                        components=list(
                            filter(
                                None,
                                [
                                    self.select_row() if self.useSelect else None,
                                    self.buttons_row() if self.useButtons else None,
                                    self.overflow_row() if self.useOverflow else None,
                                ],
                            )
                        ),
                    )
                else:
                    IncorrectDataType(
                        "ctx", "InteractionContext or commands.Context", self.ctx
                    )
            else:
                msg = await self.ctx.send(
                    content=self.content[0] if self.multiContent else self.content,
                    embed=self.pages[0],
                    components=list(
                        filter(
                            None,
                            [
                                self.select_row() if self.useSelect else None,
                                self.buttons_row() if self.useButtons else None,
                                self.overflow_row() if self.useOverflow else None,
                            ],
                        )
                    ),
                )
        # handling the interaction
        tmt = True  # stop listening when timeout expires
        start = time()
        buttonContext = None
        while tmt:
            try:
                buttonContext: ComponentContext = await wait_for_component(
                    self.bot,
                    check=self.check,
                    components=list(
                        filter(
                            None,
                            [
                                self.select_row() if self.useSelect else None,
                                self.buttons_row() if self.useButtons else None,
                                self.overflow_row() if self.useOverflow else None,
                            ],
                        )
                    ),
                    timeout=self.timeout,
                )
                if buttonContext.author not in self.successfulUsers:
                    self.successfulUsers.append(buttonContext.author)
                if buttonContext.custom_id == f"first{self.random_id}":
                    self.index = 1
                elif buttonContext.custom_id == f"prev{self.random_id}":
                    self.index = self.index - 1 or 1
                elif buttonContext.custom_id == f"next{self.random_id}":
                    self.index = self.index + 1 or self.top
                elif buttonContext.custom_id == f"last{self.random_id}":
                    self.index = self.top
                elif buttonContext.custom_id == f"select{self.random_id}":
                    self.index = int(buttonContext.selected_options[0])

                await buttonContext.edit_origin(
                    content=self.content[self.index - 1]
                    if self.multiContent
                    else self.content,
                    embed=self.pages[self.index - 1],
                    components=list(
                        filter(
                            None,
                            [
                                self.select_row() if self.useSelect else None,
                                self.buttons_row() if self.useButtons else None,
                                self.overflow_row() if self.useOverflow else None,
                            ],
                        )
                    ),
                )
            except TimeoutError:
                tmt = False
                end = time()
                if self.deleteAfterTimeout and not self.hidden:
                    await msg.edit(components=None)
                elif self.disableAfterTimeout and not self.hidden:
                    components = components = list(
                        filter(
                            None,
                            [
                                self.select_row() if self.useSelect else None,
                                self.buttons_row() if self.useButtons else None,
                                self.overflow_row() if self.useOverflow else None,
                            ],
                        )
                    )
                    for row in components:
                        for component in row["components"]:
                            component["disabled"] = True
                    await msg.edit(components=components)
                timeTaken = round(end - start)
                lastContent = (
                    self.content
                    if isinstance(self.content, (str, type(None)))
                    else self.content[self.index - 1]
                )
                lastEmbed = self.pages[self.index - 1]
                return TimedOut(
                    self.ctx,
                    buttonContext,
                    timeTaken,
                    lastContent,
                    lastEmbed,
                    self.successfulUsers,
                    self.failedUsers,
                )

    def check(self, buttonContext) -> bool:
        if self.authorOnly and buttonContext.author.id != self.ctx.author.id:
            if buttonContext.author not in self.failedUsers:
                self.failedUsers.append(buttonContext.author)
            return False
        if self.onlyFor is not None:
            check = False
            if isinstance(self.onlyFor, list):
                for user in filter(lambda x: isinstance(x, userUser), self.onlyFor):
                    check = check or user.id == buttonContext.author.id
                for role in filter(lambda x: isinstance(x, roleRole), self.onlyFor):
                    check = check or role in buttonContext.author.roles
            else:
                if isinstance(self.onlyFor, userUser):
                    check = check or self.onlyFor.id == buttonContext.author.id
                elif isinstance(self.onlyFor, roleRole):
                    check = check or self.onlyFor in buttonContext.author.roles

            if not check:
                self.failedUsers.append(buttonContext.author)
                return False

        return True

    def select_row(self) -> dict:
        select_options = []
        for i in self.pages:
            pageNum = self.pages.index(i) + 1
            try:
                title = i.title
                if title == Embed.Empty:
                    select_options.append(
                        create_select_option(
                            f"{pageNum}: Title not found", value=f"{pageNum}"
                        )
                    )
                else:
                    title = (title[:93] + "...") if len(title) > 96 else title
                    select_options.append(
                        create_select_option(f"{pageNum}: {title}", value=f"{pageNum}")
                    )
            except Exception:
                select_options.append(
                    create_select_option(
                        f"{pageNum}: Title not found", value=f"{pageNum}"
                    )
                )
        select = create_select(
            options=select_options,
            custom_id=f"select{self.random_id}",
            placeholder=f"{self.labels[2]} {self.index}/{self.top}",
            min_values=1,
            max_values=1,
        )
        selectControls = create_actionrow(select)
        return selectControls

    def buttons_row(self) -> dict:
        disableLeft = self.index == 1
        disableRight = self.index == self.top
        controlButtons = [
            # Previous Button
            create_button(
                style=self.styles[1],
                label=self.labels[1],
                custom_id=f"prev{self.random_id}",
                disabled=disableLeft,
                emoji=self.emojis[1],
            ),
            # Index
            create_button(
                style=self.styles[2],
                label=f"{self.labels[2]} {self.index}/{self.top}",
                disabled=True,
            ),
            # Next Button
            create_button(
                style=self.styles[3],
                label=self.labels[3],
                custom_id=f"next{self.random_id}",
                disabled=disableRight,
                emoji=self.emojis[2],
            ),
        ]
        if not self.useIndexButton:
            controlButtons.pop(1)
        if self.useFirstLast:
            controlButtons.insert(
                0,
                create_button(
                    style=self.styles[0],
                    label=self.labels[0],
                    custom_id=f"first{self.random_id}",
                    disabled=disableLeft,
                    emoji=self.emojis[0],
                ),
            )
            controlButtons.append(
                create_button(
                    style=self.styles[4],
                    label=self.labels[4],
                    custom_id=f"last{self.random_id}",
                    disabled=disableRight,
                    emoji=self.emojis[3],
                )
            )
        if self.useLinkButton:
            linkButton = create_button(
                style=5,
                label=self.links[0][0] if self.multiLabel else self.links[0],
                url=self.links[1][0] if self.multiURL else self.links[1],
            )
            if len(controlButtons) < 5:
                controlButtons.append(linkButton)
            elif not self.useOverflow:
                raise TooManyButtons()
        if self.useCustomButton:
            customButton = create_button(
                style=self.customButtonStyle,
                label=self.customButtonLabel,
                disabled=True,
                emoji=self.customButtonEmoji,
            )
            if len(controlButtons) < 5:
                controlButtons.append(customButton)
            elif not self.useOverflow:
                raise TooManyButtons()
        return create_actionrow(*controlButtons)

    def overflow_row(self) -> dict:
        controlButtons = []
        if self.useLinkButton:
            linkButton = create_button(
                style=5,
                label=self.links[0][0] if self.multiLabel else self.links[0],
                url=self.links[1][0] if self.multiURL else self.links[1],
            )
            if len(controlButtons) < 5:
                controlButtons.append(linkButton)
        if self.useCustomButton:
            customButton = create_button(
                style=self.customButtonStyle,
                label=self.customButtonLabel,
                disabled=True,
                emoji=self.customButtonEmoji,
            )
            if len(controlButtons) < 5:
                controlButtons.append(customButton)
        return None if controlButtons == [] else create_actionrow(*controlButtons)

    def incdata(self, name, arg, sup, supstr) -> None:
        if isinstance(arg, tuple) and isinstance(sup, tuple):
            for a in arg:
                if isinstance(a, sup):
                    return
                else:
                    raise IncorrectDataType(name[arg.index(a)], supstr, a)
        elif isinstance(arg, tuple):
            for a in arg:
                if isinstance(a, sup):
                    return
                else:
                    raise IncorrectDataType(name[arg.index(a)], supstr, a)
        else:
            if not isinstance(arg, sup):
                raise IncorrectDataType(name, supstr, arg)
