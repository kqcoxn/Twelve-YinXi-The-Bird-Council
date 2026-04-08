# 技术设计文档 TDD v0.1

## 文档信息

- **版本**: v0.1
- **基于**: PRD v0.1 第 8 章 Agent 系统设计
- **目标**: 将 Orchestrator、Memory、Planner、Knife Engine、Bell Engine 的接口和状态机细化到工程实现级别
- **技术栈**: Python + FastAPI + SQLite + 内存存储
- **部署方式**: 用户本地一键启动,无需额外安装数据库服务

---

## 1. Orchestrator 设计

### 1.1 接口定义

```python
class CouncilOrchestrator:
    """议会总控 Agent"""

    async def process_input(
        self,
        user_id: str,
        session_id: str,
        user_input: str,
        action_type: str = "submit_proposal"  # submit_proposal | supplement_testimony | ask_seat | request_reconsider | ask_summary
    ) -> CouncilResponse:
        """处理用户输入的主入口"""
        pass

    async def perceive(self, user_input: str) -> PerceptionResult:
        """感知用户意图、情绪、风险"""
        pass

    async def retrieve_memory(
        self,
        user_id: str,
        task_type: str,
        emotion_profile: dict
    ) -> MemoryContext:
        """检索相关记忆"""
        pass

    async def plan_flow(
        self,
        perception: PerceptionResult,
        memory: MemoryContext
    ) -> FlowPlan:
        """规划议会流程深度与模式"""
        pass

    async def prime_council(
        self,
        seats: List[SeatAgent],
        context: CouncilContext
    ) -> List[SeatPrevote]:
        """23 席预判"""
        pass

    async def execute_knife_cut(
        self,
        prevotes: List[SeatPrevote],
        plan: FlowPlan
    ) -> KnifeResult:
        """执行分层餐刀切分"""
        pass

    async def run_debate(
        self,
        visible_seats: List[SeatAgent],
        rounds: int = 2
    ) -> DebateTranscript:
        """执行多轮辩论"""
        pass

    async def evaluate_and_conclude(
        self,
        transcript: DebateTranscript,
        vote_map: VoteMap
    ) -> CouncilConclusion:
        """评估结果并生成结论"""
        pass

    async def render_output(
        self,
        conclusion: CouncilConclusion,
        view_types: List[str] = ["dramatic", "practical", "psychological"]
    ) -> CouncilResponse:
        """渲染多视图输出"""
        pass
```

### 1.2 状态机

```
Orchestrator State Machine:

[IDLE]
  |
  | user_input
  v
[PERCEIVING] --> [RISK_DETECTED] --> [SAFETY_MODE] --> [OUTPUT] --> [IDLE]
  |
  | normal
  v
[RETRIEVING] --> [PLANNING]
                      |
                      | light_chat
                      v
                [LIGHT_COUNCIL] --> [OUTPUT] --> [IDLE]
                      |
                      | full_deliberation
                      v
                [FULL_COUNCIL]
                      |
                      v
                [PREVOTING_23] --> [KNIFE_CUTTING] --> [DEBATING_12]
                                                              |
                                                              v
                                                        [VOTING] --> [EVALUATING]
                                                                       |
                                                                       | need_reconsider
                                                                       v
                                                                 [RECONSIDERING] --> [VOTING]
                                                                       |
                                                                       | conclude
                                                                       v
                                                                 [CONCLUDING] --> [RENDERING] --> [OUTPUT] --> [IDLE]
```

### 1.3 数据结构

```python
@dataclass
class CouncilResponse:
    session_id: str
    mode: str  # light_chat | full_council | eternal_council
    transcript: Optional[DebateTranscript]
    conclusion: CouncilConclusion
    council_state: CouncilState
    ui_commands: List[UICommand]
    memory_updates: List[MemoryWrite]

@dataclass
class PerceptionResult:
    task_type: str  # decision | emotional_sorting | chat | creative_debate | worldview_interaction
    emotion_profile: dict
    risk_flags: List[str]
    suggested_mode: str
    suggested_depth: int  # 1-3

@dataclass
class FlowPlan:
    mode: str
    rounds: int
    need_knife: bool
    output_views: List[str]
    tool_calls: List[ToolCall]
```

---

## 2. Memory 设计

### 2.1 接口定义

```python
class MemoryService:
    """分层记忆服务"""

    # Session Memory
    async def create_session(self, session_id: str, user_id: str) -> SessionMemory:
        """创建会话记忆"""
        pass

    async def update_session(
        self,
        session_id: str,
        updates: SessionUpdate
    ) -> None:
        """更新会话记忆"""
        pass

    async def get_session(self, session_id: str) -> SessionMemory:
        """获取会话记忆"""
        pass

    # User Long-term Memory
    async def get_user_profile(self, user_id: str) -> UserProfile:
        """获取用户长期画像"""
        pass

    async def update_user_profile(
        self,
        user_id: str,
        updates: UserProfileUpdate
    ) -> None:
        """更新用户画像"""
        pass

    async def search_similar_cases(
        self,
        user_id: str,
        current_issue: str,
        top_k: int = 5
    ) -> List[CaseSummary]:
        """检索相似历史议案"""
        pass

    # Seat Memory
    async def get_seat_state(
        self,
        user_id: str,
        seat_id: str
    ) -> SeatMemoryState:
        """获取席位记忆状态"""
        pass

    async def update_seat_state(
        self,
        user_id: str,
        seat_id: str,
        updates: SeatStateUpdate
    ) -> None:
        """更新席位记忆"""
        pass

    # Council Archive
    async def archive_case(self, case_record: CaseRecord) -> str:
        """归档完整案件"""
        pass

    async def query_archive(
        self,
        user_id: str,
        filters: ArchiveFilter
    ) -> List[CaseSummary]:
        """查询历史档案"""
        pass

    # Memory Write Strategy
    async def should_write_memory(
        self,
        event_type: str,
        intensity: float
    ) -> bool:
        """判断是否应该写入长期记忆"""
        pass
```

### 2.2 数据结构

```python
@dataclass
class SessionMemory:
    session_id: str
    user_id: str
    current_proposal: str
    speaking_seats: List[str]
    current_vote_map: VoteMap
    current_evidence: List[str]
    conflict_points: List[str]
    discussion_round: int
    created_at: datetime
    updated_at: datetime

@dataclass
class UserProfile:
    user_id: str
    common_issue_types: List[str]
    triggered_emotional_axes: List[str]
    preferred_output_style: str
    resonant_seats: List[str]
    major_cases: List[CaseSummary]
    created_at: datetime
    updated_at: datetime

@dataclass
class SeatMemoryState:
    seat_id: str
    user_id: str
    recent_suppression_count: int
    consecutive_minority_rounds: int
    common_oppose_issues: List[str]
    common_allies: List[str]
    user_interaction_impression: str
    last_updated: datetime

@dataclass
class CaseRecord:
    case_id: str
    user_id: str
    proposal_title: str
    conclusion: str
    minority_opinion: Optional[str]
    bell_damage_records: List[BellDamage]
    triggered_reconsider: bool
    triggered_fracture: bool
    created_at: datetime
```

### 2.3 存储策略 (轻量化方案)

```yaml
存储分层:
  Session Memory:
    存储: Python 内存字典 (dict)
    生命周期: 服务运行期间
    说明: 会话数据临时存储,重启后丢失可接受
    结构: { session_id: SessionMemory }

  User Long-term Memory:
    存储: SQLite
    表: user_profiles
    索引: user_id (主键)
    向量: 使用 sentence-transformers + 余弦相似度计算

  Seat Memory:
    存储: SQLite
    表: seat_memories
    索引: (user_id, seat_id) 复合索引

  Council Archive:
    存储: SQLite
    表: cases
    索引: user_id, created_at, conclusion_type
    向量: proposal/conclusion 使用 embedding + 简单相似度检索

优势:
  - 零配置:无需安装 Postgres/Redis
  - 单文件:所有数据存储在 council.db
  - 跨平台:Windows/Mac/Linux 完全兼容
  - 易备份:直接复制 .db 文件即可
  - 可迁移:后续需要时可平滑迁移到 Postgres
```

---

## 3. Planner 设计

### 3.1 接口定义

```python
class CouncilPlanner:
    """总控 Planner"""

    async def classify_task(self, user_input: str) -> TaskClassification:
        """识别用户任务类型"""
        pass

    async def decide_flow_depth(
        self,
        task_type: str,
        emotion_profile: dict,
        user_history: UserProfile
    ) -> FlowDepth:
        """决定流程深度"""
        pass

    async def decide_tools(
        self,
        task_type: str,
        context: MemoryContext
    ) -> List[ToolCall]:
        """决定使用的工具"""
        pass

    async def decide_output_views(
        self,
        task_type: str,
        user_preference: str
    ) -> List[str]:
        """决定输出视图"""
        pass

class SeatPlanner:
    """席位局部 Planner"""

    def __init__(self, seat_config: SeatConfig):
        self.seat_config = seat_config
        self.planner_style = self._load_planner_style()

    async def plan_action(
        self,
        current_proposal: str,
        self_state: SeatState,
        relationship_state: dict,
        current_vote_map: VoteMap,
        bell_health: int
    ) -> SeatAction:
        """规划本轮动作"""
        pass

    def _load_planner_style(self) -> PlannerStyle:
        """加载席位 Planner 风格"""
        # 不同席位有不同优先级
        # 理性: evidence > procedure > anti_groupthink
        # 内向: emotional_cost > survival > relationship
        # 刻薄: identify_self_deception > identify_hypocrisy
        # 远视: long_term_path_dependency
        # 疯狂: break_convergence > create_perturbation
        # 学者: uncertainty > model_risk
        pass
```

### 3.2 Planner 状态机

```
CouncilPlanner State Machine:

[RECEIVE_INPUT]
  |
  v
[CLASSIFY_TASK]
  |
  +-- chat --> [DECIDE_LIGHT_FLOW] --> [SELECT_TOOLS] --> [DECIDE_OUTPUT]
  |
  +-- emotional --> [DECIDE_LIGHT_FLOW] --> [SELECT_TOOLS] --> [DECIDE_OUTPUT]
  |
  +-- decision --> [DECIDE_FULL_FLOW] --> [NEED_KNIFE?] --> [SELECT_TOOLS] --> [DECIDE_OUTPUT]
  |
  +-- creative --> [DECIDE_FULL_FLOW] --> [NEED_KNIFE?] --> [SELECT_TOOLS] --> [DECIDE_OUTPUT]
  |
  +-- worldview --> [DECIDE_WORLDVIEW_FLOW] --> [SELECT_TOOLS] --> [DECIDE_OUTPUT]

SeatPlanner State Machine (per seat per round):

[RECEIVE_CONTEXT]
  |
  v
[ASSESS_STATE]
  |
  +-- bell_critical --> [PRIORITIZE_SPEAK_OR_PROTECT]
  |
  +-- minority_streak > 2 --> [DECIDE_PERSIST_OR_CONVERT]
  |
  +-- normal --> [CHOOSE_ACTION]
                    |
                    +-- speak
                    +-- question
                    +-- hold_position
                    +-- convert_vote
                    +-- withdraw
  |
  v
[GENERATE_STRUCTURED_ACTION]
  |
  v
[AWAIT_ORCHESTRATOR_DECISION]
  |
  v
[UPDATE_SELF_STATE]
```

### 3.3 Planner 配置

```python
@dataclass
class PlannerStyle:
    priority_weights: dict  # {"evidence": 0.9, "emotion": 0.3, ...}
    speak_threshold: float  # 发言阈值
    question_threshold: float  # 质询阈值
    convert_sensitivity: float  # 转票敏感度
    risk_aversion: float  # 风险厌恶度
    long_term_bias: float  # 长期倾向

@dataclass
class SeatAction:
    seat_id: str
    intent: str  # approve | oppose | abstain
    confidence: float
    proposed_action: str  # speak | question | hold | convert | withdraw
    target_seat: Optional[str]
    argument_vector: List[str]
    ask_for: Optional[str]  # delay | protection | reconsider
    stress_delta_hint: int
```

---

## 4. Knife Engine 设计

### 4.1 接口定义

```python
class KnifeEngine:
    """分层餐刀引擎"""

    async def execute_cut(
        self,
        all_seats: List[SeatState],
        prevotes: List[SeatPrevote],
        cut_mode: str,  #剧情 | decision | lottery
        council_state: CouncilState
    ) -> KnifeResult:
        """执行 23→12+11 切分"""
        pass

    async def calculate_cut_risk(
        self,
        selected_12: List[SeatState],
        hidden_11: List[SeatState]
    ) -> float:
        """计算切割风险"""
        pass

    async def validate_cut(
        self,
        knife_result: KnifeResult
    ) -> ValidationResult:
        """验证切分结果合法性"""
        pass

    def _select_by_issue_match(
        self,
        seats: List[SeatState],
        issue_type: str,
        count: int = 12
    ) -> List[SeatState]:
        """按议题匹配度选席"""
        pass

    def _select_by_user_preference(
        self,
        seats: List[SeatState],
        user_history: UserProfile,
        count: int = 12
    ) -> List[SeatState]:
        """按用户历史偏好选席"""
        pass

    def _select_by_bell_stability(
        self,
        seats: List[SeatState],
        count: int = 12
    ) -> List[SeatState]:
        """按风铃稳定度选席"""
        pass

    def _ensure_diversity(
        self,
        selected: List[SeatState],
        min_axes: int = 3
    ) -> List[SeatState]:
        """确保席位间差异度"""
        pass

    def _lottery_select(
        self,
        seats: List[SeatState],
        count: int = 12
    ) -> List[SeatState]:
        """抽签模式选席"""
        pass
```

### 4.2 切分算法

```python
def comprehensive_cut(
    seats: List[SeatState],
    prevotes: List[SeatPrevote],
    mode: str,
    weights: dict = None
) -> KnifeResult:
    """
    综合切分算法

    因子:
    - 议题类型匹配度 (weight: 0.3)
    - 用户历史偏好 (weight: 0.2)
    - 当前风铃稳定度 (weight: 0.2)
    - 席位之间差异度 (weight: 0.2)
    - 切割风险 (penalty)
    - 叙事优先级 (bonus)
    """
    if weights is None:
        weights = {
            "issue_match": 0.3,
            "user_preference": 0.2,
            "bell_stability": 0.2,
            "diversity": 0.2,
            "narrative_priority": 0.1
        }

    # 1. 计算每个席位的综合分数
    scores = []
    for seat in seats:
        score = (
            weights["issue_match"] * calculate_issue_match(seat, issue_type) +
            weights["user_preference"] * calculate_user_preference(seat, user_history) +
            weights["bell_stability"] * calculate_bell_stability(seat) +
            weights["diversity"] * calculate_diversity_contribution(seat, selected) +
            weights["narrative_priority"] * calculate_narrative_priority(seat)
        )
        scores.append((seat, score))

    # 2. 排序并选择前 12
    scores.sort(key=lambda x: x[1], reverse=True)
    selected_12 = [s[0] for s in scores[:12]]
    hidden_11 = [s[0] for s in scores[12:]]

    # 3. 计算切割风险
    risk = calculate_cut_risk(selected_12, hidden_11)

    # 4. 如果风险过高，调整选择
    if risk > 0.7:
        selected_12, hidden_11, risk = adjust_for_risk_reduction(
            selected_12, hidden_11, scores
        )

    return KnifeResult(
        visible_seats=selected_12,
        hidden_seats=hidden_11,
        cut_risk=risk,
        cut_mode=mode
    )
```

### 4.3 数据结构

```python
@dataclass
class KnifeResult:
    visible_seats: List[SeatState]
    hidden_seats: List[SeatState]
    cut_risk: float
    cut_mode: str
    cut_timestamp: datetime
    warnings: List[str]

@dataclass
class ValidationResult:
    is_valid: bool
    issues: List[str]
    suggestions: List[str]
```

### 4.4 风险计算规则

```python
def calculate_cut_risk(visible: List[SeatState], hidden: List[SeatState]) -> float:
    """
    切割风险计算

    风险因子:
    1. 席位差异度过高: variance(traits) > threshold
    2. 风铃濒危席位过多: count(bell_health < 30) > 2
    3. 连续少数派席位被隐藏: count(minority_streak > 3 in hidden) > 1
    4. 关键冲突轴断裂: missing critical axis

    返回: 0.0-1.0 风险值
    """
    risk = 0.0

    # 差异度风险
    trait_variance = calculate_trait_variance(visible)
    if trait_variance > 0.5:
        risk += 0.3

    # 风铃风险
    critical_bells = sum(1 for s in visible if s.bell_health < 30)
    if critical_bells > 2:
        risk += 0.3

    # 少数派风险
    suppressed_minority = sum(1 for s in hidden if s.minority_streak > 3)
    if suppressed_minority > 1:
        risk += 0.2

    # 冲突轴完整性
    missing_axes = check_critical_axes(visible)
    if missing_axes > 0:
        risk += 0.2 * missing_axes

    return min(risk, 1.0)
```

---

## 5. Bell Engine 设计

### 5.1 接口定义

```python
class BellEngine:
    """风铃状态引擎"""

    async def update_bell_state(
        self,
        seat_id: str,
        events: List[BellEvent],
        current_state: SeatState
    ) -> SeatState:
        """更新风铃状态"""
        pass

    async def calculate_stress_delta(
        self,
        events: List[BellEvent],
        seat_traits: dict
    ) -> int:
        """计算压力变化"""
        pass

    async def calculate_fracture_risk(
        self,
        current_stress: int,
        bell_health: int,
        suppression_count: int
    ) -> float:
        """计算碎裂风险"""
        pass

    async def apply_relief(
        self,
        seat_id: str,
        relief_type: str,
        intensity: float
    ) -> int:
        """应用压力缓解"""
        pass

    async def check_fracture(
        self,
        seat_state: SeatState
    ) -> FractureResult:
        """检查是否碎裂"""
        pass

    async def handle_fracture(
        self,
        seat_id: str,
        fracture_result: FractureResult
    ) -> SeatState:
        """处理碎裂事件"""
        pass
```

### 5.2 压力计算规则

```python
def calculate_stress_delta(
    events: List[BellEvent],
    seat_traits: dict,
    context: dict
) -> int:
    """
    压力变化计算

    压力来源:
    - 立场与多数冲突: +10~20
    - 与发言目标强碰撞: +15~25
    - 议题触发: +10~30 (根据议题类型)
    - 连续不被理解: +5/轮
    - 强制上台发言: +10
    - 被点名质疑: +15

    缓解来源:
    - 同盟支持: -10
    - 用户认同: -15
    - 主持人保护: -20
    - 转票后接纳: -10
    """
    delta = 0

    for event in events:
        if event.type == "stance_conflict":
            delta += calculate_stance_conflict_stress(event, seat_traits)
        elif event.type == "strong_collision":
            delta += 15 + random.randint(0, 10)
        elif event.type == "issue_trigger":
            delta += calculate_issue_trigger_stress(event, seat_traits)
        elif event.type == "not_understood":
            delta += 5
        elif event.type == "forced_speak":
            delta += 10
        elif event.type == "questioned":
            delta += 15
        elif event.type == "ally_support":
            delta -= 10
        elif event.type == "user_agreement":
            delta -= 15
        elif event.type == "moderator_protection":
            delta -= 20
        elif event.type == "conversion_accepted":
            delta -= 10

    # 个体差异调整
    sensitivity = seat_traits.get("stress_sensitivity", 1.0)
    delta = int(delta * sensitivity)

    return delta
```

### 5.3 碎裂判定规则

```python
def check_fracture(seat_state: SeatState) -> FractureResult:
    """
    碎裂判定

    条件:
    - fracture_risk > 0.8: 立即碎裂
    - fracture_risk > 0.6 AND stress > 80: 高概率碎裂
    - suppression_count > 5: 累积碎裂风险

    碎裂后果:
    - status: active -> fractured
    - bell_health: 降至 10-20
    - 退出当前轮次辩论
    - 可能触发重生机制 (v0.2)
    """
    risk = seat_state.fracture_risk
    stress = seat_state.stress
    suppression = seat_state.suppression_count

    if risk > 0.8:
        return FractureResult(
            will_fracture=True,
            confidence=0.95,
            reason="critical_fracture_risk"
        )
    elif risk > 0.6 and stress > 80:
        return FractureResult(
            will_fracture=True,
            confidence=0.75,
            reason="high_risk_high_stress"
        )
    elif suppression > 5:
        return FractureResult(
            will_fracture=True,
            confidence=0.6,
            reason="accumulated_suppression"
        )

    return FractureResult(
        will_fracture=False,
        confidence=1.0,
        reason="stable"
    )

@dataclass
class FractureResult:
    will_fracture: bool
    confidence: float
    reason: str
```

### 5.4 风铃状态机

```
Bell State Machine:

[HEALTHY] (bell_health > 70)
  |
  | stress accumulation
  v
[STRESSED] (bell_health: 50-70, stress: 30-50)
  |
  | continued stress OR conflict
  v
[CRITICAL] (bell_health: 30-50, stress: 50-80, fracture_risk: 0.4-0.6)
  |
  | fracture_risk > 0.6
  v
[FRACTURE_RISK] (bell_health: 20-30, stress: > 80, fracture_risk: > 0.6)
  |
  | fracture_risk > 0.8
  v
[FRACTURED] (bell_health: 10-20, status: fractured)
  |
  | recovery OR next session
  v
[RECOVERING] (bell_health: 20-40, status: silent)
  |
  | sufficient relief
  v
[HEALTHY]

状态转换规则:
- 每轮辩论后更新状态
- 碎裂后本轮退出辩论
- 静默席位不发言但可被用户查询
- 放逐席位 (exiled) 仅幕布后显示
```

### 5.5 数据结构

```python
@dataclass
class BellEvent:
    type: str  # stance_conflict | strong_collision | issue_trigger | not_understood | forced_speak | questioned | ally_support | user_agreement | moderator_protection | conversion_accepted
    source_seat_id: Optional[str]
    target_seat_id: str
    intensity: float  # 0.0-1.0
    timestamp: datetime

@dataclass
class BellState:
    bell_health: int  # 0-100
    stress: int  # 0-100
    fracture_risk: float  # 0.0-1.0
    suppression_count: int
    last_updated: datetime

@dataclass
class BellDamage:
    seat_id: str
    case_id: str
    damage_amount: int
    fracture_triggered: bool
    timestamp: datetime
```

---

## 6. 集成流程

### 6.1 完整调用链

```
User Input
  |
  v
Orchestrator.process_input()
  |
  +--> Perceive
  |      |
  |      v
  |   LLM: classify_intent, extract_emotion
  |      |
  |      v
  |   PerceptionResult
  |
  +--> Retrieve Memory
  |      |
  |      v
  |   MemoryService.get_user_profile()
  |   MemoryService.search_similar_cases()
  |      |
  |      v
  |   MemoryContext
  |
  +--> Plan Flow
  |      |
  |      v
  |   CouncilPlanner.classify_task()
  |   CouncilPlanner.decide_flow_depth()
  |      |
  |      v
  |   FlowPlan
  |
  +--> Prime Council
  |      |
  |      v
  |   For each seat in 23:
  |     SeatPlanner.plan_action()
  |      |
  |      v
  |   List[SeatPrevote]
  |
  +--> Execute Knife Cut
  |      |
  |      v
  |   KnifeEngine.execute_cut()
  |      |
  |      v
  |   KnifeResult (12 visible + 11 hidden)
  |
  +--> Run Debate (2-3 rounds)
  |      |
  |      v
  |   For each round:
  |     For each visible seat:
  |       SeatPlanner.plan_action()
  |       LLM: generate_speech()
  |       BellEngine.update_bell_state()
  |       MemoryService.update_session()
  |      |
  |      v
  |   DebateTranscript
  |
  +--> Vote
  |      |
  |      v
  |   VoteEngine.tally_votes()
  |      |
  |      v
  |   VoteMap
  |
  +--> Evaluate
  |      |
  |      +-- need_reconsider? --> Run Debate (additional round)
  |      |
  |      +-- conclude
  |             |
  |             v
  |          CouncilConclusion
  |
  +--> Render Output
  |      |
  |      v
  |   NarrativeRenderer.render_dramatic()
  |   NarrativeRenderer.render_practical()
  |   NarrativeRenderer.render_psychological()
  |      |
  |      v
  |   CouncilResponse
  |
  +--> Write Memory
         |
         v
      MemoryService.archive_case()
      MemoryService.update_user_profile()
      MemoryService.update_seat_state()
```

### 6.2 WebSocket 实时推送

```python
class CouncilWebSocketHandler:
    """WebSocket 实时推送"""

    async def handle_connection(self, websocket: WebSocket):
        await websocket.accept()

        # 订阅议会事件流
        event_stream = self.orchestrator.get_event_stream()

        async for event in event_stream:
            if event.type == "seat_speaking":
                await websocket.send_json({
                    "type": "seat_highlight",
                    "seat_id": event.seat_id,
                    "speech": event.speech
                })
            elif event.type == "bell_update":
                await websocket.send_json({
                    "type": "bell_animation",
                    "seat_id": event.seat_id,
                    "bell_health": event.bell_health,
                    "fracture_risk": event.fracture_risk
                })
            elif event.type == "vote_update":
                await websocket.send_json({
                    "type": "vote_map_update",
                    "vote_map": event.vote_map
                })
            elif event.type == "knife_cut":
                await websocket.send_json({
                    "type": "knife_animation",
                    "visible_seats": event.visible_seats,
                    "hidden_seats": event.hidden_seats,
                    "cut_risk": event.cut_risk
                })
            elif event.type == "conclusion":
                await websocket.send_json({
                    "type": "conclusion",
                    "conclusion": event.conclusion,
                    "views": event.views
                })
```

---

## 7. 错误处理与重试

### 7.1 LLM 调用失败

```python
async def call_llm_with_retry(
    prompt: str,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> LLMResponse:
    """LLM 调用重试机制"""
    for attempt in range(max_retries):
        try:
            response = await llm_client.generate(prompt)
            return response
        except LLMError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = backoff_factor ** attempt
            await asyncio.sleep(wait_time)
```

### 7.2 状态不一致处理

```python
async def validate_council_state(state: CouncilState) -> ValidationResult:
    """验证议会状态一致性"""
    issues = []

    # 检查席位数量
    if len(state.visible_seats) != 12:
        issues.append(f"Visible seats count {len(state.visible_seats)} != 12")

    # 检查票型总和
    vote_total = sum(state.vote_map.values())
    if vote_total != len(state.visible_seats):
        issues.append(f"Vote total {vote_total} != visible seats {len(state.visible_seats)}")

    # 检查风铃状态范围
    for seat in state.visible_seats:
        if not (0 <= seat.bell_health <= 100):
            issues.append(f"Seat {seat.seat_id} bell_health out of range")

    return ValidationResult(
        is_valid=len(issues) == 0,
        issues=issues
    )
```

---

## 8. 性能优化

### 8.1 批量处理

```python
async def batch_prevote_23_seats(seats: List[SeatAgent]) -> List[SeatPrevote]:
    """批量 23 席预判 (并发调用)"""
    tasks = [seat.predict_stance() for seat in seats]
    prevotes = await asyncio.gather(*tasks, return_exceptions=True)
    return [p for p in prevotes if not isinstance(p, Exception)]
```

### 8.2 缓存策略

```yaml
缓存层 (内存实现):
  User Profile:
    存储: Python dict + 简单 LRU 缓存
    更新: 每次重大议案归档后刷新
    实现: functools.lru_cache 或 cachetools

  Seat Memory:
    存储: Python dict
    更新: 每次席位状态变更后刷新

  Similar Cases:
    存储: Python dict (带 TTL)
    更新: 每次新议案归档后刷新
    实现: cachetools.TTLCache

说明:
  - 内存缓存无需额外服务
  - 服务重启后缓存自动重建
  - 对本地单用户场景完全够用
```

### 8.3 数据库索引 (SQLite)

```sql
-- SQLite 索引优化
-- 用户档案索引
CREATE INDEX IF NOT EXISTS idx_user_profile_user_id ON user_profiles(user_id);

-- 席位记忆索引
CREATE INDEX IF NOT EXISTS idx_seat_memory_composite ON seat_memories(user_id, seat_id);

-- 议案归档索引
CREATE INDEX IF NOT EXISTS idx_cases_user_created ON cases(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cases_conclusion_type ON cases(conclusion_type);

-- 向量检索:
-- SQLite 不原生支持 HNSW,使用以下方案:
-- 1. 存储 embedding 为 BLOB
-- 2. 使用 sentence-transformers 计算余弦相似度
-- 3. 对小规模数据(<1000条),全表扫描性能可接受
-- 4. 后续可集成 sqlite-vec 扩展优化
```

---

## 9. 测试策略

### 9.1 单元测试

```python
def test_bell_engine_stress_calculation():
    """测试风铃压力计算"""
    engine = BellEngine()
    events = [
        BellEvent(type="stance_conflict", intensity=0.8),
        BellEvent(type="ally_support", intensity=1.0)
    ]
    delta = engine.calculate_stress_delta(events, {"stress_sensitivity": 1.0})
    assert delta > 0  # 冲突压力应大于同盟缓解

def test_knife_engine_cut_risk():
    """测试切割风险计算"""
    visible = [create_seat(bell_health=80) for _ in range(12)]
    hidden = [create_seat(bell_health=20) for _ in range(11)]
    risk = calculate_cut_risk(visible, hidden)
    assert risk < 0.5  # 前台稳定应低风险
```

### 9.2 集成测试

```python
async def test_full_council_flow():
    """测试完整议会流程"""
    orchestrator = CouncilOrchestrator()
    response = await orchestrator.process_input(
        user_id="test_user",
        session_id="test_session",
        user_input="我要不要换工作?",
        action_type="submit_proposal"
    )

    assert response.mode == "full_council"
    assert response.conclusion is not None
    assert len(response.ui_commands) > 0
```

### 9.3 评估测试

```python
def test_seat_voice_distinction():
    """测试席位口吻区分度"""
    seats = load_23_seats()
    speeches = [generate_speech(seat, "测试议题") for seat in seats]

    # 使用 embedding 计算相似度
    similarities = calculate_pairwise_similarity(speeches)
    avg_similarity = np.mean(similarities)

    assert avg_similarity < 0.7  # 口吻应有明显差异
```

---

## 10. 部署架构

### 10.1 服务架构 (单体应用)

```yaml
单体应用 (本地部署优化):
  main.py:
    职责: 统一入口,启动所有服务
    包含:
      - FastAPI 后端服务
      - 静态文件服务 (前端构建产物)
      - SQLite 数据库连接管理
      - 内存缓存管理
      - 自动打开浏览器

  优势:
    - 一行命令启动: python main.py
    - 无需 Docker/容器编排
    - 无需安装数据库服务
    - 适合本地使用和小规模部署

  后续扩展:
    - 如需云端部署,可拆分为微服务
    - SQLite 可迁移到 Postgres
    - 内存缓存可替换为 Redis
```

### 10.2 环境变量 (简化版)

```bash
# LLM 配置 (必需)
FAST_MODEL_API_KEY=xxx
FAST_MODEL_ENDPOINT=xxx
STRONG_MODEL_API_KEY=xxx
STRONG_MODEL_ENDPOINT=xxx

# 数据库 (SQLite 自动创建,无需配置)
# DATABASE_URL=sqlite:///./data/council.db  # 可选,有默认值

# 会话配置
SESSION_TTL=86400
MAX_DEBATE_ROUNDS=3

# 服务配置
HOST=127.0.0.1
PORT=8000
AUTO_OPEN_BROWSER=true  # 启动后自动打开浏览器
```

---

## 11. 后续迭代计划

### v0.2

- 重生机制 (fractured seats recovery)
- 关系网络可视化
- 复杂切分策略 (基于图谱)
- 席位自定义配置

### v0.3

- 全息 3D 场景
- 全量配音
- 多语言支持
- 移动端适配

### v1.0

- 完整剧情模式
- 用户社区
- 议案分享
- 数据分析后台

---

## 附录 A: 完整类型定义

详见 PRD v0.1 第 14 章数据结构草案 + 本文档各章节数据结构定义。

## 附录 B: API 端点清单

```
POST /api/v1/council/submit
POST /api/v1/council/supplement
POST /api/v1/council/ask-seat
POST /api/v1/council/reconsider
POST /api/v1/council/summary
GET  /api/v1/council/session/{session_id}
GET  /api/v1/council/history
GET  /api/v1/user/profile
GET  /api/v1/seats/{seat_id}/state
WS   /ws/council/{session_id}
```

## 附录 C: 错误码定义

```
1001: 用户未找到
1002: 会话已过期
2001: 风铃状态异常
2002: 切割风险过高
3001: LLM 调用失败
3002: 投票状态不一致
4001: 安全风险检测
4002: 高风险输入
```

---

## 附录 D: 前端预构建策略

### 开发 vs 生产工作流

```yaml
开发者工作流:
  开发模式:
    - 前端: cd frontend && npm run dev (localhost:3000)
    - 后端: cd backend && uvicorn app.main:app --reload (localhost:8000)
    - 特点: 热重载,快速迭代,前后端分离

  构建模式:
    - 命令: cd frontend && npm run build
    - 输出: ../frontend-dist/ 目录
    - 验证: 检查构建产物是否正确
    - 提交: git add frontend-dist/ && git commit

用户工作流:
  - pip install -r requirements.txt
  - python main.py
  - 浏览器自动打开 http://localhost:8000
  - 无需 Node.js,无需构建
```

### 为什么预构建?

**用户体验优先:**

- ✅ 零 Node.js 依赖
- ✅ 一行命令启动
- ✅ 避免构建失败
- ✅ 减少安装时间 (从 5 分钟降到 30 秒)

**开发者体验:**

- ✅ 开发时仍有热重载
- ✅ CI/CD 自动构建验证
- ✅ 版本控制构建产物

### 自动化构建脚本

```bash
# scripts/build-frontend.sh (Linux/Mac)
#!/bin/bash
echo "🔨 构建前端..."
cd frontend
npm install
npm run build
cd ..
echo "✅ 前端构建完成: frontend-dist/"

# scripts/build-frontend.ps1 (Windows)
Write-Host "🔨 构建前端..." -ForegroundColor Cyan
Set-Location frontend
npm install
npm run build
Set-Location ..
Write-Host "✅ 前端构建完成: frontend-dist/" -ForegroundColor Green
```

---

## 附录 E: 可选依赖与降级策略

### 依赖分层

```txt
核心依赖 (必需) - requirements.txt:
  fastapi==0.115.0
  uvicorn==0.30.0
  pydantic==2.8.0
  aiosqlite==0.20.0
  cachetools==5.5.0
  openai>=1.0.0
  litellm>=1.40.0
  python-dotenv==1.0.0

增强依赖 (可选) - requirements-vector.txt:
  sentence-transformers>=3.0.0
  torch>=2.0.0
  numpy>=1.24.0

开发依赖 (可选) - requirements-dev.txt:
  pytest>=7.0.0
  pytest-asyncio>=0.23.0
  black>=24.0.0
  ruff>=0.5.0
```

### 向量检索降级实现

```python
# app/services/vector_search.py
from typing import List, Optional
import sqlite3

try:
    from sentence_transformers import SentenceTransformer, util
    HAS_VECTOR_SEARCH = True
except ImportError:
    HAS_VECTOR_SEARCH = False

class VectorSearchService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.model = None

        if HAS_VECTOR_SEARCH:
            try:
                # 使用轻量级模型 (~80MB)
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ 向量检索已启用")
            except Exception as e:
                print(f"⚠️  向量模型加载失败: {e}")
                print("💡 降级为文本匹配模式")
        else:
            print("⚠️  向量检索未安装")
            print("💡 安装: pip install -r requirements-vector.txt")

    async def search_similar_cases(
        self,
        user_id: str,
        query: str,
        top_k: int = 5
    ) -> List[dict]:
        """检索相似案例 (自动降级)"""
        if self.model is not None:
            return await self._vector_search(user_id, query, top_k)
        else:
            return await self._text_search(user_id, query, top_k)

    async def _vector_search(
        self,
        user_id: str,
        query: str,
        top_k: int
    ) -> List[dict]:
        """向量检索 (高精度)"""
        # 1. 计算查询向量
        query_embedding = self.model.encode(query, convert_to_tensor=True)

        # 2. 从数据库获取所有案例
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT case_id, proposal_title, conclusion, proposal_embedding "
                "FROM cases WHERE user_id = ? AND proposal_embedding IS NOT NULL",
                (user_id,)
            )
            rows = await cursor.fetchall()

        # 3. 计算相似度并排序
        results = []
        for row in rows:
            if row[3]:  # embedding 存在
                case_embedding = torch.tensor(row[3])
                similarity = util.cos_sim(query_embedding, case_embedding).item()
                results.append({
                    'case_id': row[0],
                    'proposal_title': row[1],
                    'conclusion': row[2],
                    'similarity': similarity
                })

        # 4. 返回 top_k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]

    async def _text_search(
        self,
        user_id: str,
        query: str,
        top_k: int
    ) -> List[dict]:
        """文本检索 (降级方案)"""
        # 使用 SQLite LIKE 进行简单关键词匹配
        keywords = query.split()

        async with aiosqlite.connect(self.db_path) as db:
            # 构建 WHERE 子句
            conditions = []
            params = [user_id]

            for keyword in keywords:
                conditions.append(
                    "(proposal_title LIKE ? OR conclusion LIKE ?)"
                )
                params.extend([f'%{keyword}%', f'%{keyword}%'])

            where_clause = " AND ".join(conditions)

            cursor = await db.execute(
                f"SELECT case_id, proposal_title, conclusion "
                f"FROM cases WHERE user_id = ? AND ({where_clause}) "
                f"ORDER BY created_at DESC LIMIT ?",
                params + [top_k]
            )
            rows = await cursor.fetchall()

        return [
            {
                'case_id': row[0],
                'proposal_title': row[1],
                'conclusion': row[2],
                'similarity': 0.0  # 无相似度分数
            }
            for row in rows
        ]
```

### 启动提示

```python
# app/main.py
from app.services.vector_search import HAS_VECTOR_SEARCH

@app.on_event("startup")
async def startup():
    print("\n" + "="*50)
    print("🐦 十二音希: 群鸟议会")
    print("="*50)

    # 检查向量检索
    if not HAS_VECTOR_SEARCH:
        print("⚠️  向量检索: 未安装 (使用文本匹配)")
        print("💡 增强安装: pip install -r requirements-vector.txt")
    else:
        print("✅ 向量检索: 已启用")

    # 初始化数据库
    await init_db()

    print(f"\n🌐 服务地址: http://{settings.HOST}:{settings.PORT}")
    print("📖 API 文档: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止服务\n")
```

---

## 附录 F: 数据库自动初始化

### 初始化脚本

```python
# app/core/database.py
import aiosqlite
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / "data" / "council.db"
DB_VERSION = 1

async def init_db():
    """首次启动自动初始化数据库"""
    # 确保 data 目录存在
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        # 用户档案表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                common_issue_types TEXT DEFAULT '[]',
                triggered_emotional_axes TEXT DEFAULT '[]',
                preferred_output_style TEXT DEFAULT 'dramatic',
                resonant_seats TEXT DEFAULT '[]',
                major_cases TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 席位记忆表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS seat_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                seat_id TEXT NOT NULL,
                recent_suppression_count INTEGER DEFAULT 0,
                consecutive_minority_rounds INTEGER DEFAULT 0,
                common_oppose_issues TEXT DEFAULT '[]',
                common_allies TEXT DEFAULT '[]',
                user_interaction_impression TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, seat_id)
            )
        """)

        # 议会档案表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                proposal_title TEXT NOT NULL,
                conclusion TEXT,
                minority_opinion TEXT,
                triggered_reconsider BOOLEAN DEFAULT FALSE,
                triggered_fracture BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                proposal_embedding BLOB,
                conclusion_embedding BLOB
            )
        """)

        # 创建索引
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_seat_memory_user_seat
            ON seat_memories(user_id, seat_id)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_cases_user_created
            ON cases(user_id, created_at DESC)
        """)

        # 版本表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS db_version (
                version INTEGER PRIMARY KEY
            )
        """)
        await db.execute(
            "INSERT OR IGNORE INTO db_version (version) VALUES (?)",
            (DB_VERSION,)
        )

        await db.commit()

    print(f"✅ 数据库已初始化: {DB_PATH}")

async def backup_db():
    """备份数据库"""
    import shutil
    from datetime import datetime

    backup_dir = DB_PATH.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"council_{timestamp}.db"

    if DB_PATH.exists():
        shutil.copy2(DB_PATH, backup_path)
        print(f"💾 数据库已备份: {backup_path}")
```

### 数据备份策略

```bash
# 手动备份
cp data/council.db data/backups/council_$(date +%Y%m%d).db

# 自动备份 (可选,每次启动时)
# 在 main.py 中调用 backup_db()

# 清理旧备份 (保留 7 天)
find data/backups/ -name "council_*.db" -mtime +7 -delete
```
