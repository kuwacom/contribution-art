from __future__ import annotations

import argparse
import hashlib
import os
import random
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from pathlib import Path
from typing import Final
from zoneinfo import ZoneInfo


"""GitHub のコントリビューショングラフへ文字を描くための CLI"""


DAY_NAMES: Final[tuple[str, ...]] = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
FIXED_OFFSET_ALIASES: Final[dict[str, str]] = {
    "UTC": "+00:00",
    "ETC/UTC": "+00:00",
    "ASIA/TOKYO": "+09:00",
    "JAPAN": "+09:00",
}

FONT_5X7: Final[dict[str, tuple[str, ...]]] = {
    " ": ("...", "...", "...", "...", "...", "...", "..."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", "..##.", "..##."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("#####", "....#", "...#.", "..##.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#...#", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "#...#", ".###."),
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
}
FONT_7X7: Final[dict[str, tuple[str, ...]]] = {
    " ": (".......", ".......", ".......", ".......", ".......", ".......", "......."),
    "-": (".......", ".......", ".......", "..###..", ".......", ".......", "......."),
    ".": (".......", ".......", ".......", ".......", ".......", "...##..", "...##.."),
    "A": ("..###..", ".#...#.", "#.....#", "#.....#", "#######", "#.....#", "#.....#"),
    "B": ("######.", "#.....#", "#.....#", "######.", "#.....#", "#.....#", "######."),
    "C": (".#####.", "#.....#", "#......", "#......", "#......", "#.....#", ".#####."),
    "D": ("######.", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#", "######."),
    "E": ("#######", "#......", "#......", "######.", "#......", "#......", "#######"),
    "F": ("#######", "#......", "#......", "######.", "#......", "#......", "#......"),
    "G": (".#####.", "#.....#", "#......", "#..####", "#.....#", "#.....#", ".#####."),
    "H": ("#.....#", "#.....#", "#.....#", "#######", "#.....#", "#.....#", "#.....#"),
    "I": (".#####.", "...#...", "...#...", "...#...", "...#...", "...#...", ".#####."),
    "J": ("..#####", "....#..", "....#..", "....#..", "#...#..", "#...#..", ".###..."),
    "K": ("#....#.", "#...#..", "#..#...", "###....", "#..#...", "#...#..", "#....#."),
    "L": ("#......", "#......", "#......", "#......", "#......", "#......", "#######"),
    "M": ("#.....#", "##...##", "#.#.#.#", "#..#..#", "#.....#", "#.....#", "#.....#"),
    "N": ("#.....#", "##....#", "#.#...#", "#..#..#", "#...#.#", "#....##", "#.....#"),
    "O": (".#####.", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#", ".#####."),
    "P": ("######.", "#.....#", "#.....#", "######.", "#......", "#......", "#......"),
    "Q": (".#####.", "#.....#", "#.....#", "#.....#", "#..#..#", "#...#.#", ".#####."),
    "R": ("######.", "#.....#", "#.....#", "######.", "#..#...", "#...#..", "#....#."),
    "S": (".#####.", "#.....#", "#......", ".#####.", "......#", "#.....#", ".#####."),
    "T": ("#######", "...#...", "...#...", "...#...", "...#...", "...#...", "...#..."),
    "U": ("#.....#", "#.....#", "#.....#", "#.....#", "#.....#", "#.....#", ".#####."),
    "V": ("#.....#", "#.....#", "#.....#", "#.....#", ".#...#.", "..#.#..", "...#..."),
    "W": ("#.....#", "#.....#", "#.....#", "#..#..#", "#.#.#.#", "##...##", "#.....#"),
    "X": ("#.....#", ".#...#.", "..#.#..", "...#...", "..#.#..", ".#...#.", "#.....#"),
    "Y": ("#.....#", ".#...#.", "..#.#..", "...#...", "...#...", "...#...", "...#..."),
    "Z": ("#######", "....#..", "...#...", "..#....", ".#.....", "#......", "#######"),
}


@dataclass(frozen=True)
class CliConfig:
    """CLI から受け取った設定値をまとめる"""

    text: str
    startDate: date
    endDate: date
    fontName: str
    timeStart: time
    timeEnd: time
    timezoneName: str
    minCommits: int
    maxCommits: int
    seed: int
    apply: bool
    push: bool
    resetBranchHistory: bool
    remote: str
    branch: str
    showDates: bool


@dataclass(frozen=True)
class DayPlan:
    """1 日ぶんのコミット計画を表す"""

    targetDate: date
    commitCount: int
    timestamps: tuple[datetime, ...]


@dataclass(frozen=True)
class GraphPlan:
    """描画領域全体の計画を表す"""

    requestedStartDate: date
    requestedEndDate: date
    drawingStartDate: date
    drawingEndDate: date
    availableColumns: int
    textColumns: int
    leftPaddingColumns: int
    gridRows: tuple[str, ...]
    dayPlans: tuple[DayPlan, ...]
    totalCommits: int


def main() -> int:
    """CLI 全体の流れを制御する"""

    try:
        cliConfig = parseArgs()
        graphPlan = buildGraphPlan(cliConfig)
        printPlan(graphPlan, cliConfig)

        if not cliConfig.apply:
            print("\nプレビューのみです")
            print("実際にコミットを作る場合は --apply を付けてください")
            return 0

        ensureCleanWorkingTree()
        if cliConfig.resetBranchHistory:
            resetBranchHistory(cliConfig, graphPlan)
        createCommits(graphPlan, cliConfig)

        if cliConfig.push:
            pushCommits(cliConfig)

        print("\n完了しました")
        return 0
    except ContributionArtError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("error: 中断されました", file=sys.stderr)
        return 130


class ContributionArtError(Exception):
    """CLI の想定エラーをまとめるための例外"""


def parseArgs() -> CliConfig:
    """引数と .env を読み込み安全に扱える設定へ正規化する"""

    envValues = loadEnvFile(Path.cwd() / ".env")
    parser = argparse.ArgumentParser(
        description="GitHub contribution graph に文字を描く空コミットを生成する",
    )
    parser.add_argument("text", help="描画したい文字列")
    parser.add_argument("--start-date", required=True, help="期間の開始日 例: 2026-06-07")
    parser.add_argument("--end-date", required=True, help="期間の終了日 例: 2026-09-26")
    parser.add_argument("--font", choices=("5x7", "7x7"), default="5x7", help="文字のマス目サイズ")
    parser.add_argument("--time-start", default=getEnvValue(envValues, "CONTRIBUTION_ART_TIME_START", "19:30"))
    parser.add_argument("--time-end", default=getEnvValue(envValues, "CONTRIBUTION_ART_TIME_END", "22:30"))
    parser.add_argument("--timezone", default=getEnvValue(envValues, "CONTRIBUTION_ART_TIMEZONE", "+09:00"))
    parser.add_argument("--min-commits", type=int, default=getEnvInt(envValues, "CONTRIBUTION_ART_MIN_COMMITS", 3))
    parser.add_argument("--max-commits", type=int, default=getEnvInt(envValues, "CONTRIBUTION_ART_MAX_COMMITS", 6))
    parser.add_argument("--seed", type=int, default=None, help="同じ見た目を再現したいときの乱数シード")
    parser.add_argument("--apply", action="store_true", help="実際に空コミットを作る")
    parser.add_argument("--push", action="store_true", help="作成後に push する")
    parser.add_argument(
        "--reset-branch-history",
        action="store_true",
        help="現在ブランチの履歴を作り直してからコミットする",
    )
    parser.add_argument("--remote", default=getEnvValue(envValues, "CONTRIBUTION_ART_REMOTE", "origin"))
    parser.add_argument("--branch", default=getEnvValue(envValues, "CONTRIBUTION_ART_BRANCH", detectCurrentBranch()))
    parser.add_argument("--show-dates", action="store_true", help="コミット日ごとの計画も表示する")
    parsedArgs = parser.parse_args()

    if parsedArgs.push and not parsedArgs.apply:
        raise ContributionArtError("--push を使う場合は --apply も必要です")

    if parsedArgs.reset_branch_history and not parsedArgs.apply:
        raise ContributionArtError("--reset-branch-history を使う場合は --apply も必要です")

    startDate = parseDate(parsedArgs.start_date)
    endDate = parseDate(parsedArgs.end_date)

    if endDate < startDate:
        raise ContributionArtError("終了日は開始日以降にしてください")

    timeStart = parseTimeValue(parsedArgs.time_start)
    timeEnd = parseTimeValue(parsedArgs.time_end)

    if datetime.combine(date.today(), timeEnd) <= datetime.combine(date.today(), timeStart):
        raise ContributionArtError("終了時刻は開始時刻より後にしてください")

    if parsedArgs.min_commits < 1:
        raise ContributionArtError("min-commits は 1 以上にしてください")

    if parsedArgs.max_commits < parsedArgs.min_commits:
        raise ContributionArtError("max-commits は min-commits 以上にしてください")

    seed = parsedArgs.seed
    if seed is None:
        seed = buildDefaultSeed(parsedArgs.text, startDate, endDate)

    validateTimezone(parsedArgs.timezone)

    return CliConfig(
        text=parsedArgs.text,
        startDate=startDate,
        endDate=endDate,
        fontName=parsedArgs.font,
        timeStart=timeStart,
        timeEnd=timeEnd,
        timezoneName=parsedArgs.timezone,
        minCommits=parsedArgs.min_commits,
        maxCommits=parsedArgs.max_commits,
        seed=seed,
        apply=parsedArgs.apply,
        push=parsedArgs.push,
        resetBranchHistory=parsedArgs.reset_branch_history,
        remote=parsedArgs.remote,
        branch=parsedArgs.branch,
        showDates=parsedArgs.show_dates,
    )


def buildGraphPlan(cliConfig: CliConfig) -> GraphPlan:
    """文字列を週グリッドへ配置し日別のコミット計画へ変換する"""

    drawingStartDate = alignToNextSunday(cliConfig.startDate)
    drawingEndDate = alignToPreviousSaturday(cliConfig.endDate)

    if drawingStartDate > drawingEndDate:
        raise ContributionArtError("指定期間の中に 1 週間ぶんの描画領域がありません")

    availableColumns = ((drawingEndDate - drawingStartDate).days + 1) // 7
    normalizedText = normalizeText(cliConfig.text)
    gridRows = buildTextGrid(normalizedText, cliConfig.fontName)
    textColumns = len(gridRows[0])

    if textColumns > availableColumns:
        raise ContributionArtError(
            f"文字列が長すぎます 必要列数 {textColumns} に対して利用可能列数は {availableColumns} です"
        )

    # 余白を左右均等に近づけて見た目を安定させる
    leftPaddingColumns = (availableColumns - textColumns) // 2
    timezoneInfo = buildTimezoneInfo(cliConfig.timezoneName)
    randomizer = random.Random(cliConfig.seed)
    dayPlans = createDayPlans(
        gridRows=gridRows,
        drawingStartDate=drawingStartDate,
        leftPaddingColumns=leftPaddingColumns,
        timezoneInfo=timezoneInfo,
        timeStart=cliConfig.timeStart,
        timeEnd=cliConfig.timeEnd,
        minCommits=cliConfig.minCommits,
        maxCommits=cliConfig.maxCommits,
        randomizer=randomizer,
    )
    totalCommits = sum(dayPlan.commitCount for dayPlan in dayPlans)

    return GraphPlan(
        requestedStartDate=cliConfig.startDate,
        requestedEndDate=cliConfig.endDate,
        drawingStartDate=drawingStartDate,
        drawingEndDate=drawingEndDate,
        availableColumns=availableColumns,
        textColumns=textColumns,
        leftPaddingColumns=leftPaddingColumns,
        gridRows=gridRows,
        dayPlans=dayPlans,
        totalCommits=totalCommits,
    )


def printPlan(graphPlan: GraphPlan, cliConfig: CliConfig) -> None:
    """実行前に配置結果とコミット計画を見やすく表示する"""

    print("=== contribution art plan ===")
    print(f"text: {normalizeText(cliConfig.text)}")
    print(f"requested range: {graphPlan.requestedStartDate} -> {graphPlan.requestedEndDate}")
    print(f"drawing range:   {graphPlan.drawingStartDate} -> {graphPlan.drawingEndDate}")
    print(f"columns: {graphPlan.textColumns} / {graphPlan.availableColumns}")
    print(f"font: {cliConfig.fontName}")
    print(f"active days: {len(graphPlan.dayPlans)}")
    print(f"total commits: {graphPlan.totalCommits}")
    print(f"time window: {cliConfig.timeStart.strftime('%H:%M')} - {cliConfig.timeEnd.strftime('%H:%M')} {cliConfig.timezoneName}")
    print(f"seed: {cliConfig.seed}")
    print(f"reset branch history: {'yes' if cliConfig.resetBranchHistory else 'no'}")
    print("")

    renderedRows = renderPreviewRows(graphPlan.gridRows)
    for index, row in enumerate(renderedRows):
        print(f"{DAY_NAMES[index]}  {row}")

    if cliConfig.showDates:
        print("")
        for dayPlan in graphPlan.dayPlans:
            firstTimestamp = dayPlan.timestamps[0].strftime("%Y-%m-%d %H:%M")
            lastTimestamp = dayPlan.timestamps[-1].strftime("%H:%M")
            print(
                f"{dayPlan.targetDate}  commits={dayPlan.commitCount}  "
                f"window={firstTimestamp} .. {lastTimestamp}"
            )


def renderPreviewRows(gridRows: tuple[str, ...]) -> tuple[str, ...]:
    """内部表現のグリッドをターミナル向けの見た目へ変換する"""

    rendered: list[str] = []
    for row in gridRows:
        rendered.append("".join("██" if cell == "#" else "  " for cell in row))
    return tuple(rendered)


def createDayPlans(
    *,
    gridRows: tuple[str, ...],
    drawingStartDate: date,
    leftPaddingColumns: int,
    timezoneInfo: tzinfo,
    timeStart: time,
    timeEnd: time,
    minCommits: int,
    maxCommits: int,
    randomizer: random.Random,
) -> tuple[DayPlan, ...]:
    """塗られたマスを日付へ対応付けて日別計画を作る"""

    dayPlans: list[DayPlan] = []
    width = len(gridRows[0])

    for columnIndex in range(width):
        weekOffset = leftPaddingColumns + columnIndex
        for rowIndex, row in enumerate(gridRows):
            if row[columnIndex] != "#":
                continue

            # GitHub のグラフは 1 列が 1 週間なので列を週単位で日付へ変換する
            targetDate = drawingStartDate + timedelta(days=(weekOffset * 7) + rowIndex)
            commitCount = randomizer.randint(minCommits, maxCommits)
            timestamps = buildTimestampsForDate(
                targetDate=targetDate,
                timezoneInfo=timezoneInfo,
                timeStart=timeStart,
                timeEnd=timeEnd,
                commitCount=commitCount,
                randomizer=randomizer,
            )
            dayPlans.append(
                DayPlan(
                    targetDate=targetDate,
                    commitCount=commitCount,
                    timestamps=timestamps,
                )
            )

    dayPlans.sort(key=lambda dayPlan: dayPlan.timestamps[0])
    return tuple(dayPlans)


def buildTimestampsForDate(
    *,
    targetDate: date,
    timezoneInfo: tzinfo,
    timeStart: time,
    timeEnd: time,
    commitCount: int,
    randomizer: random.Random,
) -> tuple[datetime, ...]:
    """1 日の中で自然に見える複数のコミット時刻を生成する"""

    startDateTime = datetime.combine(targetDate, timeStart, tzinfo=timezoneInfo)
    endDateTime = datetime.combine(targetDate, timeEnd, tzinfo=timezoneInfo)
    totalSeconds = int((endDateTime - startDateTime).total_seconds())

    if totalSeconds <= 0:
        raise ContributionArtError("時刻範囲の計算に失敗しました")

    interval = totalSeconds / (commitCount + 1)
    # 均等配置に少し揺らぎを加えて機械的な見た目を避ける
    jitterRange = max(30, int(min(interval / 3, 20 * 60)))
    timestamps: list[datetime] = []

    for commitIndex in range(commitCount):
        targetOffset = int(interval * (commitIndex + 1))
        jitter = randomizer.randint(-jitterRange, jitterRange)
        secondOffset = max(0, min(totalSeconds - 1, targetOffset + jitter))
        timestamp = startDateTime + timedelta(seconds=secondOffset)

        # 秒単位でも前後が逆転しないよう最小限だけ押し出す
        if timestamps and timestamp <= timestamps[-1]:
            timestamp = timestamps[-1] + timedelta(seconds=1)

        timestamps.append(timestamp)

    return tuple(timestamps)


def createCommits(graphPlan: GraphPlan, cliConfig: CliConfig) -> None:
    """計画に従って空コミットを順番に作成する"""

    totalCommits = graphPlan.totalCommits
    commitNumber = 0

    for dayPlan in graphPlan.dayPlans:
        for timestamp in dayPlan.timestamps:
            commitNumber += 1
            commitMessage = (
                f"art: {normalizeText(cliConfig.text)} "
                f"{dayPlan.targetDate.isoformat()} "
                f"({commitNumber}/{totalCommits})"
            )
            gitDate = timestamp.isoformat()
            runGitCommand(
                [
                    "git",
                    "commit",
                    "--allow-empty",
                    "--message",
                    commitMessage,
                    "--date",
                    gitDate,
                ],
                extraEnv={
                    # author と committer を揃えないと GitHub 上の表示が意図とずれることがある
                    "GIT_AUTHOR_DATE": gitDate,
                    "GIT_COMMITTER_DATE": gitDate,
                },
            )


def resetBranchHistory(cliConfig: CliConfig, graphPlan: GraphPlan) -> None:
    """現在ブランチを現在ツリーの 1 コミットへ作り直してから描画を始める"""

    currentBranchName = requireCurrentBranchName()
    timestampSuffix = datetime.now().strftime("%Y%m%d%H%M%S")
    backupBranchName = f"{currentBranchName}-backup-{timestampSuffix}"
    temporaryBranchName = f"{currentBranchName}-reset-{timestampSuffix}"
    timezoneInfo = buildTimezoneInfo(cliConfig.timezoneName)
    baseCommitDate = datetime.combine(
        graphPlan.requestedStartDate - timedelta(days=1),
        time(hour=12, minute=0),
        tzinfo=timezoneInfo,
    ).isoformat()

    runGitCommand(["git", "branch", backupBranchName, currentBranchName])
    runGitCommand(["git", "switch", "--orphan", temporaryBranchName])
    runGitCommand(["git", "add", "-A"])
    runGitCommand(
        [
            "git",
            "commit",
            "--message",
            f"chore: reset contribution art base ({backupBranchName})",
            "--date",
            baseCommitDate,
        ],
        extraEnv={
            # ベースコミットを対象期間の外へ置いて描画範囲を汚さないようにする
            "GIT_AUTHOR_DATE": baseCommitDate,
            "GIT_COMMITTER_DATE": baseCommitDate,
        },
    )
    runGitCommand(["git", "branch", "-M", currentBranchName])


def pushCommits(cliConfig: CliConfig) -> None:
    """現在の HEAD を指定ブランチへ push する"""

    pushCommand = ["git", "push"]
    if cliConfig.resetBranchHistory:
        # 履歴を作り直した場合は通常 push では拒否されるため明示的に強制する
        pushCommand.append("--force-with-lease")
    pushCommand.extend([cliConfig.remote, f"HEAD:{cliConfig.branch}"])
    runGitCommand(pushCommand)


def ensureCleanWorkingTree() -> None:
    """空コミットへ作業中の差分が混ざる事故を防ぐ"""

    result = runCommand(
        ["git", "status", "--porcelain"],
        captureOutput=True,
    )
    if result.stdout.strip():
        raise ContributionArtError(
            "作業ツリーに変更があります 空コミットへ混ざる事故を避けるため --apply を中止しました"
        )


def runGitCommand(command: list[str], extraEnv: dict[str, str] | None = None) -> None:
    """Git コマンド専用の薄いラッパー"""

    runCommand(command, captureOutput=False, extraEnv=extraEnv)


def runCommand(
    command: list[str],
    *,
    captureOutput: bool,
    extraEnv: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """外部コマンドを実行し失敗時は扱いやすい例外へ変換する"""

    processEnv = os.environ.copy()
    if extraEnv is not None:
        processEnv.update(extraEnv)

    result = subprocess.run(
        command,
        check=False,
        capture_output=captureOutput,
        text=True,
        env=processEnv,
    )

    if result.returncode != 0:
        stderrText = result.stderr.strip() if result.stderr else ""
        stdoutText = result.stdout.strip() if result.stdout else ""
        detailText = stderrText or stdoutText or f"終了コード {result.returncode}"
        joinedCommand = " ".join(command)
        raise ContributionArtError(f"コマンドに失敗しました: {joinedCommand}\n{detailText}")

    return result


def buildTextGrid(text: str, fontName: str) -> tuple[str, ...]:
    """文字列を 7 行固定のドットグリッドへ変換する"""

    font = getFont(fontName)
    gridRows = [""] * 7

    for characterIndex, character in enumerate(text):
        glyph = font.get(character)
        if glyph is None:
            raise ContributionArtError(f"未対応の文字です: {character}")

        if characterIndex > 0:
            # 7x7 は列数をぴったり合わせたい用途があるため文字間隔を詰める
            gapWidth = 0 if fontName == "7x7" else 1
            for rowIndex in range(7):
                gridRows[rowIndex] += "." * gapWidth

        for rowIndex in range(7):
            gridRows[rowIndex] += glyph[rowIndex]

    return tuple(row.replace("#", "#").replace(" ", ".") for row in gridRows)


def getFont(fontName: str) -> dict[str, tuple[str, ...]]:
    """指定名に対応するフォント定義を返す"""

    if fontName == "7x7":
        return FONT_7X7
    return FONT_5X7


def normalizeText(text: str) -> str:
    """入力文字列を描画用に正規化する"""

    normalizedText = " ".join(text.strip().upper().split())
    if not normalizedText:
        raise ContributionArtError("文字列が空です")
    return normalizedText


def alignToNextSunday(targetDate: date) -> date:
    """開始日を GitHub グラフの列境界である日曜へ揃える"""

    daysUntilSunday = (6 - targetDate.weekday()) % 7
    return targetDate + timedelta(days=daysUntilSunday)


def alignToPreviousSaturday(targetDate: date) -> date:
    """終了日を GitHub グラフの列境界である土曜へ揃える"""

    daysSinceSaturday = (targetDate.weekday() - 5) % 7
    return targetDate - timedelta(days=daysSinceSaturday)


def parseDate(rawValue: str) -> date:
    """ISO 形式の日付文字列を安全に date へ変換する"""

    try:
        return date.fromisoformat(rawValue)
    except ValueError as error:
        raise ContributionArtError(f"日付の形式が不正です: {rawValue}") from error


def parseTimeValue(rawValue: str) -> time:
    """HH:MM 形式の文字列を time へ変換する"""

    try:
        hourText, minuteText = rawValue.split(":", maxsplit=1)
        hour = int(hourText)
        minute = int(minuteText)
        return time(hour=hour, minute=minute)
    except ValueError as error:
        raise ContributionArtError(f"時刻の形式が不正です: {rawValue}") from error


def validateTimezone(timezoneName: str) -> None:
    """タイムゾーン指定が解決可能かを事前に検証する"""

    try:
        buildTimezoneInfo(timezoneName)
    except Exception as error:
        raise ContributionArtError(f"タイムゾーンが不正です: {timezoneName}") from error


def buildTimezoneInfo(timezoneName: str) -> tzinfo:
    """IANA 名か固定オフセットから tzinfo を構築する"""

    try:
        return ZoneInfo(timezoneName)
    except Exception:
        # Windows では IANA 名がそのまま解決できないことがあるため別名を補う
        aliasValue = FIXED_OFFSET_ALIASES.get(timezoneName.upper())
        if aliasValue is not None:
            return parseFixedOffsetTimezone(aliasValue, timezoneName)
        return parseFixedOffsetTimezone(timezoneName, timezoneName)


def parseFixedOffsetTimezone(rawValue: str, displayName: str) -> tzinfo:
    """+09:00 のような固定オフセット文字列を tzinfo へ変換する"""

    sign = 1
    offsetValue = rawValue

    if rawValue.startswith("-"):
        sign = -1
        offsetValue = rawValue[1:]
    elif rawValue.startswith("+"):
        offsetValue = rawValue[1:]

    hourText, separator, minuteText = offsetValue.partition(":")
    if separator != ":":
        raise ContributionArtError(f"タイムゾーンの形式が不正です: {displayName}")

    hour = int(hourText)
    minute = int(minuteText)

    if hour > 23 or minute > 59:
        raise ContributionArtError(f"タイムゾーンの形式が不正です: {displayName}")

    deltaValue = timedelta(hours=hour, minutes=minute) * sign
    return timezone(deltaValue, name=displayName)


def buildDefaultSeed(text: str, startDate: date, endDate: date) -> int:
    """同じ入力なら同じ配置になる既定シードを作る"""

    seedSource = f"{normalizeText(text)}|{startDate.isoformat()}|{endDate.isoformat()}"
    digest = hashlib.sha256(seedSource.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def detectCurrentBranch() -> str:
    """明示指定がない場合に現在ブランチを既定値として使う"""

    try:
        result = runCommand(
            ["git", "branch", "--show-current"],
            captureOutput=True,
        )
    except ContributionArtError:
        return "main"

    branchName = result.stdout.strip()
    return branchName or "main"


def requireCurrentBranchName() -> str:
    """履歴を書き換える前に現在ブランチ名を厳密に取得する"""

    result = runCommand(
        ["git", "branch", "--show-current"],
        captureOutput=True,
    )
    branchName = result.stdout.strip()
    if not branchName:
        raise ContributionArtError("detached HEAD では --reset-branch-history を使えません")
    return branchName


def loadEnvFile(envPath: Path) -> dict[str, str]:
    """依存を増やさず最小限の .env を読み込む"""

    envValues: dict[str, str] = {}
    if not envPath.exists():
        return envValues

    for rawLine in envPath.read_text(encoding="utf-8").splitlines():
        strippedLine = rawLine.strip()
        if not strippedLine or strippedLine.startswith("#"):
            continue

        key, separator, value = strippedLine.partition("=")
        if separator != "=":
            continue

        envValues[key.strip()] = value.strip()

    return envValues


def getEnvValue(envValues: dict[str, str], key: str, fallback: str) -> str:
    """環境変数を優先しつつ .env と既定値をフォールバックする"""

    return os.environ.get(key, envValues.get(key, fallback))


def getEnvInt(envValues: dict[str, str], key: str, fallback: int) -> int:
    """整数値の環境変数を読み込み型を保ったまま返す"""

    rawValue = os.environ.get(key, envValues.get(key))
    if rawValue is None:
        return fallback

    try:
        return int(rawValue)
    except ValueError as error:
        raise ContributionArtError(f".env の値が整数ではありません: {key}={rawValue}") from error


if __name__ == "__main__":
    raise SystemExit(main())
