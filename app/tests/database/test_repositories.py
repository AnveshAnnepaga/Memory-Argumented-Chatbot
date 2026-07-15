# File: app/tests/database/test_repositories.py
import pytest
from datetime import datetime, timezone
from app.domain.user import (
    User,
    UserProfile,
    Session,
    KnowledgeSource,
    EvaluationResult,
    ConfigurationItem,
)
from app.domain.conversation import (
    Conversation,
    Message,
    MemorySnapshot,
    ToolExecutionHistory,
    RouterDecisionHistory,
    PromptHistoryItem,
)
from app.domain.knowledge import Document, Chunk, KnowledgeVector, SemanticMemoryVector
from app.domain.graph import GraphNode, GraphRelationship, Entity, Relationship
from app.repositories import (
    UserRepository,
    UserProfileRepository,
    SessionRepository,
    KnowledgeSourceRepository,
    EvaluationRepository,
    ConfigurationRepository,
    ConversationRepository,
    MessageRepository,
    MemorySnapshotRepository,
    ToolHistoryRepository,
    RouterHistoryRepository,
    PromptHistoryRepository,
    VectorRepository,
    KnowledgeRepository,
    SemanticMemoryRepository,
    GraphRepository,
    EntityRepository,
    RelationshipRepository,
)


@pytest.mark.asyncio
async def test_postgres_repositories():
    """Verify PostgreSQL repository operations (User, Profile, Session, Source, Evaluation, Config)."""
    # 1. UserRepository
    user_repo = UserRepository()
    user = User(id="u1", username="john_doe", email="john@example.com", password_hash="hashed")
    created_user = await user_repo.create(user)
    assert created_user.id == "u1"
    assert created_user.email == "john@example.com"
    
    retrieved_user = await user_repo.retrieve("u1")
    assert retrieved_user is not None and retrieved_user.username == "john_doe"
    
    found_by_email = await user_repo.find_by_email("john@example.com")
    assert found_by_email is not None and found_by_email.id == "u1"
    
    updated_user = await user_repo.update("u1", {"is_active": False})
    assert updated_user is not None and updated_user.is_active is False
    assert await user_repo.exists("u1") is True
    assert await user_repo.count() >= 1

    # 2. UserProfileRepository
    profile_repo = UserProfileRepository()
    profile = await profile_repo.store_preferences("u1", {"theme": "dark", "notifications": True})
    assert profile.user_id == "u1"
    assert profile.preferences["theme"] == "dark"

    # 3. SessionRepository
    session_repo = SessionRepository()
    sess = Session(id="s1", user_id="u1", token="tok123")
    await session_repo.create(sess)
    active = await session_repo.get_active_sessions("u1")
    assert len(active) == 1 and active[0].id == "s1"
    await session_repo.close_session("s1")
    active_after_close = await session_repo.get_active_sessions("u1")
    assert len(active_after_close) == 0

    # 4. KnowledgeSourceRepository
    ks_repo = KnowledgeSourceRepository()
    ks = KnowledgeSource(id="ks1", source_type="web", uri="https://example.com", name="Example Doc")
    await ks_repo.register_source(ks)
    await ks_repo.update_crawl_status("ks1", "completed")
    await ks_repo.track_crawl_history("ks1", {"status": "success", "pages_crawled": 5})
    retrieved_ks = await ks_repo.retrieve("ks1")
    assert retrieved_ks is not None and retrieved_ks.status == "completed"
    assert len(retrieved_ks.crawl_history) == 1

    # 5. EvaluationRepository
    eval_repo = EvaluationRepository()
    ev = EvaluationResult(id="ev1", conversation_id="c1", metric_name="faithfulness", score=0.95, reasoning="Good accuracy")
    await eval_repo.save_metrics(ev)
    history = await eval_repo.fetch_evaluation_history(conversation_id="c1")
    assert len(history) == 1 and history[0].score == 0.95

    # 6. ConfigurationRepository
    config_repo = ConfigurationRepository()
    cfg = await config_repo.update_runtime_configuration("max_retries", 3, description="API retry limit")
    assert cfg.value == 3
    read_cfg = await config_repo.read_configuration("max_retries")
    assert read_cfg is not None and read_cfg.value == 3


@pytest.mark.asyncio
async def test_mongodb_repositories():
    """Verify MongoDB repository operations (Conversation, Message, MemorySnapshot, ToolHistory, RouterHistory, PromptHistory)."""
    # 1. ConversationRepository
    conv_repo = ConversationRepository()
    conv = Conversation(id="c1", user_id="u1", title="First Chat")
    await conv_repo.create(conv)
    await conv_repo.update_summary("c1", "Discussed AI architecture.")
    retrieved_conv = await conv_repo.retrieve("c1")
    assert retrieved_conv is not None and retrieved_conv.summary == "Discussed AI architecture."

    # 2. MessageRepository
    msg_repo = MessageRepository()
    msg1 = Message(id="m1", conversation_id="c1", role="user", content="Hello")
    msg2 = Message(id="m2", conversation_id="c1", role="assistant", content="Hi there!")
    await msg_repo.store_messages([msg1, msg2])
    msgs = await msg_repo.retrieve_messages("c1")
    assert len(msgs) == 2
    deleted_count = await msg_repo.delete_by_conversation("c1")
    assert deleted_count == 2

    # 3. MemorySnapshotRepository
    mem_repo = MemorySnapshotRepository()
    snap = MemorySnapshot(id="snap1", user_id="u1", episodic_content="User likes Python.")
    await mem_repo.store_episodic_memory(snap)
    snaps = await mem_repo.retrieve_snapshots("u1")
    assert len(snaps) == 1
    await mem_repo.archive_snapshot("snap1")
    unarchived = await mem_repo.retrieve_snapshots("u1", include_archived=False)
    assert len(unarchived) == 0

    # 4. ToolHistoryRepository
    tool_repo = ToolHistoryRepository()
    th = ToolExecutionHistory(id="th1", conversation_id="c1", tool_name="search_web", execution_time_ms=120.5)
    await tool_repo.save_tool_execution(th)
    retrieved_th = await tool_repo.retrieve_tool_history(conversation_id="c1")
    assert len(retrieved_th) == 1 and retrieved_th[0].tool_name == "search_web"

    # 5. RouterHistoryRepository
    router_repo = RouterHistoryRepository()
    rh = RouterDecisionHistory(id="rh1", conversation_id="c1", query="Find docs", chosen_route="rag_search", confidence_score=0.88)
    await router_repo.save_routing_decision(rh)
    analytics = await router_repo.retrieve_routing_analytics(conversation_id="c1")
    assert len(analytics) == 1 and analytics[0].chosen_route == "rag_search"

    # 6. PromptHistoryRepository
    prompt_repo = PromptHistoryRepository()
    ph = PromptHistoryItem(id="ph1", conversation_id="c1", prompt_template_name="system_prompt", model_name="llama-3-70b", rendered_prompt="System: Act as AI.")
    await prompt_repo.store_prompt(ph)
    prompts = await prompt_repo.retrieve_prompts("c1")
    assert len(prompts) == 1 and prompts[0].model_name == "llama-3-70b"


@pytest.mark.asyncio
async def test_pinecone_repositories():
    """Verify Pinecone vector and knowledge repositories."""
    # 1. VectorRepository
    v_repo = VectorRepository()
    kv = KnowledgeVector(id="v1", values=[0.1, 0.2, 0.3], metadata={"source": "test"})
    await v_repo.store_embeddings([kv], namespace="test_ns")
    similar = await v_repo.search_similar_vectors([0.1, 0.2, 0.3], top_k=5, namespace="test_ns")
    assert len(similar) >= 1

    # 2. KnowledgeRepository
    k_repo = KnowledgeRepository(vector_repo=v_repo, namespace="knowledge_ns")
    c = Chunk(id="chk1", document_id="doc1", chunk_index=0, text_content="FastAPI architecture")
    await k_repo.store_chunks([c], [[0.5, 0.5, 0.5]])
    retrieved_chunks = await k_repo.retrieve_context([0.5, 0.5, 0.5], top_k=3)
    assert len(retrieved_chunks) == 1 and retrieved_chunks[0].text_content == "FastAPI architecture"
    by_source = await k_repo.filter_chunks_by_source("doc1")
    assert len(by_source) == 1

    # 3. SemanticMemoryRepository
    sm_repo = SemanticMemoryRepository(vector_repo=v_repo, namespace="semantic_ns")
    sm = SemanticMemoryVector(id="sm1", user_id="u1", memory_text="User prefers asynchronous code.", values=[0.9, 0.1, 0.0])
    await sm_repo.store_semantic_memory(sm)
    searched_sm = await sm_repo.search_memory("u1", [0.9, 0.1, 0.0])
    assert len(searched_sm) == 1 and searched_sm[0].memory_text == "User prefers asynchronous code."


@pytest.mark.asyncio
async def test_neo4j_repositories():
    """Verify Neo4j graph and entity/relationship repositories."""
    # 1. GraphRepository
    g_repo = GraphRepository()
    node_a = GraphNode(id="na", label="Person", properties={"id": "na", "name": "Alice"})
    node_b = GraphNode(id="nb", label="Concept", properties={"id": "nb", "name": "FastAPI"})
    await g_repo.create_node(node_a)
    await g_repo.create_node(node_b)
    rel = GraphRelationship(id="r1", source_node_id="na", target_node_id="nb", relationship_type="KNOWS", properties={"id": "r1", "years": 3})
    await g_repo.create_relationship(rel)
    traversed = await g_repo.traverse_relationships("na", relationship_type="KNOWS")
    assert len(traversed) == 1 and traversed[0].id == "nb"

    # 2. EntityRepository & RelationshipRepository
    e_repo = EntityRepository(graph_repo=g_repo)
    r_repo = RelationshipRepository(graph_repo=g_repo, entity_repo=e_repo)
    
    ent_1 = Entity(id="e1", name="Bob", entity_type="Person")
    ent_2 = Entity(id="e2", name="LangGraph", entity_type="Tool")
    await e_repo.store_extracted_entity(ent_1)
    await e_repo.store_extracted_entity(ent_2)
    
    persons = await e_repo.find_entities_by_type("Person")
    assert any(p.name == "Bob" for p in persons)
    
    rel_entity = Relationship(id="re1", source_entity_id="e1", target_entity_id="e2", relation_type="USES", weight=0.9)
    await r_repo.store_relationship(rel_entity)
    
    connected = await r_repo.find_connected_entities("e1")
    assert any(c.id == "e2" for c in connected)
    
    subgraph = await r_repo.get_subgraph("e1")
    assert "nodes" in subgraph and "relationships" in subgraph
