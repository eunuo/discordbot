import random
import discord
from discord import app_commands
from discord.ext import commands
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


import random
import discord
from discord import app_commands
from discord.ext import commands
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"로그인 완료: {bot.user}")


# =========================
# 음성채널 감시
# =========================

# 특정 유저 전용 문구 (디스코드 유저 ID: {문구 리스트})
SPECIAL_JOIN_MESSAGES = {
    # 123456789012345678: ["특별 입장 문구1 {name}", "특별 입장 문구2 {name}"],
    215383922886836225: ["야릇한 {name}의 등장", "{name}엉덩이 만지기"],
    259535729728815114: ["야생의 네모가 나타났다!", "모두 대학원생을 조심해"]
}
SPECIAL_LEAVE_MESSAGES = {
    # 123456789012345678: ["특별 퇴장 문구1 {name}", "특별 퇴장 문구2 {name}"],
}

JOIN_MESSAGES = [
    "🚨 {name} 등장. 다들 숨으세요.",
    "😱 {name} 나타남. 긴장하세요.",
    "🎺 {name} 입장. 박수 쳐주세요.",
    "👀 {name} 왔다. 조심해.",
    "🔔 {name} 접속. 오늘도 수고.",
]

LEAVE_MESSAGES = [
    "🎉 {name} 퇴장. 평화가 찾아왔습니다.",
    "😌 {name} 나갔다. 이제 편하다.",
    "👋 {name} 퇴장. 잘 가요~",
    "🕊 {name} 사라짐. 고요함이 흐릅니다.",
    "🚪 {name} 퇴장. 문 닫아줘.",
]

MOVE_MESSAGES = [
    "🔄 {name} 이동: {before} → {after}",
    "🏃 {name} 도망침: {before} → {after}",
    "🚶 {name} 자리 옮김: {before} → {after}",
]


@bot.event
async def on_voice_state_update(member, before, after):
    log_channel = discord.utils.get(member.guild.text_channels, name="참가기록")
    if log_channel is None:
        return

    if before.channel is None and after.channel is not None:
        pool = SPECIAL_JOIN_MESSAGES.get(member.id, JOIN_MESSAGES)
        msg = random.choice(pool).format(name=member.display_name)
        await log_channel.send(msg)

    elif before.channel is not None and after.channel is None:
        pool = SPECIAL_LEAVE_MESSAGES.get(member.id, LEAVE_MESSAGES)
        msg = random.choice(pool).format(name=member.display_name)
        await log_channel.send(msg)

    elif before.channel != after.channel:
        msg = random.choice(MOVE_MESSAGES).format(
            name=member.display_name,
            before=before.channel.name,
            after=after.channel.name
        )
        await log_channel.send(msg)


# =========================
# 제비뽑기
# =========================
@bot.tree.command(name="제비뽑기", description="현재 음성채널 사람 중 한 명을 랜덤으로 뽑습니다.")
async def draw_lots(interaction: discord.Interaction):
    user = interaction.user

    if not isinstance(user, discord.Member):
        await interaction.response.send_message("서버 안에서만 사용할 수 있습니다.", ephemeral=True)
        return

    if user.voice is None or user.voice.channel is None:
        await interaction.response.send_message("먼저 음성채널에 들어가야 합니다.", ephemeral=True)
        return

    voice_channel = user.voice.channel
    members = [m for m in voice_channel.members if not m.bot]

    if len(members) == 0:
        await interaction.response.send_message("뽑을 사람이 없습니다.", ephemeral=True)
        return

    winner = random.choice(members)

    await interaction.response.send_message(
        f"🎯 **제비뽑기 결과**\n\n"
        f"채널: **{voice_channel.name}**\n"
        f"참가자 수: **{len(members)}명**\n\n"
        f"🏆 당첨자: **{winner.display_name}**"
    )

# =========================
# 롤 라인 랜덤 배정
# =========================
@bot.tree.command(name="랜덤라인", description="현재 음성채널 사람 중 5명에게 롤 라인을 랜덤 배정합니다.")
async def lol_lane(interaction: discord.Interaction):
    user = interaction.user

    if not isinstance(user, discord.Member):
        await interaction.response.send_message("서버 안에서만 사용할 수 있습니다.", ephemeral=True)
        return

    if user.voice is None or user.voice.channel is None:
        await interaction.response.send_message("먼저 음성채널에 들어가야 합니다.", ephemeral=True)
        return

    voice_channel = user.voice.channel
    members = [m for m in voice_channel.members if not m.bot]

    if len(members) < 5:
        await interaction.response.send_message(
            f"인원이 부족합니다.\n현재 인원: **{len(members)}명**\n필요 인원: **5명**",
            ephemeral=True
        )
        return

    selected_members = random.sample(members, 5)
    lanes = ["TOP(탑)", "AD(원딜)", "SUP(서폿)", "MID(미드)", "JUG(정글)"]
    random.shuffle(lanes)

    result = "🎮 **롤 라인 랜덤 배정**\n\n"

    for member, lane in zip(selected_members, lanes):
        result += f"**{lane}** : {member.display_name}\n"

    if len(members) > 5:
        leftovers = [m for m in members if m not in selected_members]
        result += "\n## 제외된 인원\n"
        for member in leftovers:
            result += f"- {member.display_name}\n"

    await interaction.response.send_message(result)



# =========================
# 음성채널 추방투표
# =========================
class KickVoteView(discord.ui.View):
    def __init__(self, target: discord.Member, voice_channel: discord.VoiceChannel):
        super().__init__(timeout=10)
        self.target = target
        self.voice_channel = voice_channel
        self.yes_votes = set()
        self.no_votes = set()
        self.message = None

    def current_members(self):
        return [m for m in self.voice_channel.members if not m.bot]

    async def update_message(self):
        members = self.current_members()
        needed = (len(members) // 2) + 1

        await self.message.edit(
            content=(
                f"🚨 **음성채널 추방투표**\n\n"
                f"대상: **{self.target.display_name}**\n"
                f"채널: **{self.voice_channel.name}**\n\n"
                f"찬성: **{len(self.yes_votes)}** / 필요: **{needed}**\n"
                f"반대: **{len(self.no_votes)}**\n\n"
                f"10초 안에 과반수 찬성 시 음성채널에서 추방됩니다."
            ),
            view=self
        )

    async def finish_vote(self):
        members = self.current_members()
        needed = (len(members) // 2) + 1

        for item in self.children:
            item.disabled = True

        if self.target.voice is None or self.target.voice.channel != self.voice_channel:
            result = f"⚠ 대상자가 이미 음성채널에 없습니다: **{self.target.display_name}**"

        elif len(self.yes_votes) >= needed and len(self.yes_votes) > len(self.no_votes):
            await self.target.move_to(None)
            result = f"💥 투표 통과. **{self.target.display_name}** 님을 음성채널에서 추방했습니다."

        else:
            result = f"🛡 투표 부결. **{self.target.display_name}** 님은 살아남았습니다."

        await self.message.edit(content=result, view=self)

    @discord.ui.button(label="찬성", style=discord.ButtonStyle.green)
    async def vote_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        voter = interaction.user

        if not isinstance(voter, discord.Member):
            await interaction.response.send_message("서버 안에서만 투표할 수 있습니다.", ephemeral=True)
            return

        if voter.voice is None or voter.voice.channel != self.voice_channel:
            await interaction.response.send_message("같은 음성채널에 있는 사람만 투표할 수 있습니다.", ephemeral=True)
            return

        self.no_votes.discard(voter.id)
        self.yes_votes.add(voter.id)

        await interaction.response.send_message("찬성 투표 완료.", ephemeral=True)
        await self.update_message()

    @discord.ui.button(label="반대", style=discord.ButtonStyle.red)
    async def vote_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        voter = interaction.user

        if not isinstance(voter, discord.Member):
            await interaction.response.send_message("서버 안에서만 투표할 수 있습니다.", ephemeral=True)
            return

        if voter.voice is None or voter.voice.channel != self.voice_channel:
            await interaction.response.send_message("같은 음성채널에 있는 사람만 투표할 수 있습니다.", ephemeral=True)
            return

        self.yes_votes.discard(voter.id)
        self.no_votes.add(voter.id)

        await interaction.response.send_message("반대 투표 완료.", ephemeral=True)
        await self.update_message()

    async def on_timeout(self):
        if self.message:
            await self.finish_vote()


@bot.tree.command(name="추방투표", description="현재 음성채널의 특정 유저를 추방하는 투표를 시작합니다.")
@app_commands.describe(target="추방 투표 대상")
async def kick_vote(interaction: discord.Interaction, target: discord.Member):
    user = interaction.user

    if not isinstance(user, discord.Member):
        await interaction.response.send_message("서버 안에서만 사용할 수 있습니다.", ephemeral=True)
        return

    if user.voice is None or user.voice.channel is None:
        await interaction.response.send_message("먼저 음성채널에 들어가야 합니다.", ephemeral=True)
        return

    voice_channel = user.voice.channel

    if target.bot:
        await interaction.response.send_message("봇은 대상으로 지정할 수 없습니다.", ephemeral=True)
        return

    if target.voice is None or target.voice.channel != voice_channel:
        await interaction.response.send_message("대상자가 같은 음성채널에 있어야 합니다.", ephemeral=True)
        return

    if target.id == user.id:
        await interaction.response.send_message("본인은 추방투표 대상으로 지정할 수 없습니다.", ephemeral=True)
        return

    view = KickVoteView(target, voice_channel)

    await interaction.response.send_message(
        f"🚨 **음성채널 추방투표 시작**\n\n"
        f"대상: **{target.display_name}**\n"
        f"채널: **{voice_channel.name}**\n\n"
        f"찬성: **0**\n"
        f"반대: **0**\n\n"
        f"10초 안에 과반수 찬성 시 음성채널에서 추방됩니다.",
        view=view
    )

    view.message = await interaction.original_response()


# =========================
# 팀 나누기
# =========================
class TeamMoveView(discord.ui.View):
    def __init__(self, team_assignments: dict[int, str], guild: discord.Guild):
        super().__init__(timeout=300)
        self.team_assignments = team_assignments
        self.guild = guild

    @discord.ui.button(label="내 팀으로 이동", style=discord.ButtonStyle.blurple)
    async def move_to_my_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user

        if not isinstance(user, discord.Member):
            await interaction.response.send_message("서버 안에서만 사용할 수 있습니다.", ephemeral=True)
            return

        if user.id not in self.team_assignments:
            await interaction.response.send_message("팀 배정 대상자가 아닙니다.", ephemeral=True)
            return

        if user.voice is None or user.voice.channel is None:
            await interaction.response.send_message("먼저 음성채널에 들어가야 이동할 수 있습니다.", ephemeral=True)
            return

        team_name = self.team_assignments[user.id]
        target_channel = discord.utils.get(self.guild.voice_channels, name=team_name)

        if target_channel is None:
            await interaction.response.send_message(
                f"음성채널 **{team_name}** 을 찾을 수 없습니다.",
                ephemeral=True
            )
            return

        await user.move_to(target_channel)
        await interaction.response.send_message(
            f"✅ **{team_name}** 채널로 이동했습니다.",
            ephemeral=True
        )


@bot.tree.command(name="팀나누기", description="현재 음성채널 인원을 랜덤으로 팀 나누기 합니다.")
@app_commands.describe(
    team_count="나눌 팀 수. 현재는 1팀, 2팀, 3팀 기준",
    members_per_team="한 팀당 인원"
)
async def divide_teams(
    interaction: discord.Interaction,
    team_count: app_commands.Range[int, 1, 3],
    members_per_team: app_commands.Range[int, 1, 99]
):
    user = interaction.user

    if not isinstance(user, discord.Member):
        await interaction.response.send_message("서버 안에서만 사용할 수 있습니다.", ephemeral=True)
        return

    if user.voice is None or user.voice.channel is None:
        await interaction.response.send_message("먼저 음성채널에 들어가야 합니다.", ephemeral=True)
        return

    voice_channel = user.voice.channel
    members = [m for m in voice_channel.members if not m.bot]

    required_count = team_count * members_per_team

    if len(members) < required_count:
        await interaction.response.send_message(
            f"인원이 부족합니다.\n"
            f"필요 인원: **{required_count}명**\n"
            f"현재 인원: **{len(members)}명**",
            ephemeral=True
        )
        return

    random.shuffle(members)
    selected_members = members[:required_count]
    leftover_members = members[required_count:]

    teams = {}
    team_assignments = {}

    for i in range(team_count):
        team_name = f"{i + 1}팀"
        start = i * members_per_team
        end = start + members_per_team
        team_members = selected_members[start:end]

        teams[team_name] = team_members

        for member in team_members:
            team_assignments[member.id] = team_name

    result = "🎲 **팀 나누기 결과**\n\n"

    for team_name, team_members in teams.items():
        result += f"## {team_name}\n"
        for member in team_members:
            result += f"- {member.display_name}\n"
        result += "\n"

    if leftover_members:
        result += "## 남는 인원\n"
        for member in leftover_members:
            result += f"- {member.display_name}\n"
        result += "\n"

    result += "아래 버튼을 누르면 본인 팀 음성채널로 이동합니다."

    view = TeamMoveView(team_assignments, interaction.guild)

    await interaction.response.send_message(result, view=view)


# =========================
# 게임서버 버튼 토대
# =========================
class GameServerPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="게임서버 개설", style=discord.ButtonStyle.green)
    async def create_server(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🟩 게임서버 개설 요청 접수됨.\n아직 실제 서버 실행 명령은 연결하지 않았습니다.",
            ephemeral=True
        )

    @discord.ui.button(label="서버 종료", style=discord.ButtonStyle.red)
    async def stop_server(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🟥 서버 종료 요청 접수됨.\n아직 실제 종료 명령은 연결하지 않았습니다.",
            ephemeral=True
        )

    @discord.ui.button(label="서버 상태 확인", style=discord.ButtonStyle.blurple)
    async def server_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "📡 서버 상태: 미연결",
            ephemeral=True
        )


@bot.tree.command(name="서버패널", description="게임서버 관리 버튼을 표시합니다.")
async def server_panel(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🎮 게임서버 관리 패널",
        view=GameServerPanel()
    )


bot.run(TOKEN)