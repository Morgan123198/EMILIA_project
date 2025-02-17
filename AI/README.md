# AI Development Plan - Emilia Project

This directory contains the AI components of the Emilia project, focusing on the implementation of intelligent agents and natural language processing capabilities.

## Development Phases

### Phase 1: Core NLP Implementation
- [ ] Set up base LLM integration
  - Implement API connection to chosen LLM (e.g., LLaMA 2)
  - Configure model parameters and response formatting
  - Implement prompt engineering templates
- [ ] Develop conversation management
  - Create conversation state handlers
  - Implement context retention mechanisms
  - Design conversation flow controllers

### Phase 2: Specialized Agents Development
- [ ] Emotional Support Agent
  - Implement sentiment analysis
  - Develop emotional state tracking
  - Create response templates for different emotional states
  - Integrate CBT techniques and mindfulness exercises
  - Implement content recommendation system:
    - Mindfulness videos (e.g., TAKEASIT_, APRENDEMOSJUNTOSBBVA)
    - Relaxation exercises from curated channels
    - Anxiety management resources (e.g., breathing exercises, mental anchoring)
    - Motivational content (e.g., EMPRENDE.BROTHERS, LUIS_FRANQUEZA)
    - Therapeutic content (e.g., WALTER_RISO, MENTESEXPERTAS)

- [ ] Academic Planning Agent
  - Develop task organization algorithms
  - Implement study schedule optimization
  - Create stress management recommendations
  - Integrate time management content:
    - Weekly planning resources (e.g., "ORGANIZACIÓN SEMANAL" videos)
    - Time blocking techniques (based on Bill Gates method)
    - Goal-setting methodologies (e.g., "BÚSQUEDA DEL SENTIDO DE TU VIDA")
    - Productivity enhancement videos

- [ ] Crisis Management Agent
  - Implement emergency response protocols
  - Create escalation mechanisms
  - Develop safety check systems
  - Integrate emergency resources:
    - Anxiety management exercises (e.g., anclaje technique videos)
    - Stress relief exercises (e.g., breathing techniques)
    - Crisis support content
    - Professional help references

### Phase 3: Content Management System
- [ ] Resource Database
  - Structure content categories:
    - Mindfulness and Relaxation
    - Time Management and Organization
    - Motivation and Personal Growth
    - Crisis Management
  - Implement content metadata:
    - Video duration
    - Content summaries
    - Source attribution
    - Topic categorization
  - Create content update pipeline

- [ ] Recommendation Engine
  - Design recommendation algorithms based on:
    - User emotional state
    - Academic context
    - Time of day/week
    - Previous interactions
  - Implement content matching system
  - Create engagement tracking

### Phase 4: Memory and State Management
- [ ] Implement Memory Manager
  - Design conversation history storage
  - Create retrieval mechanisms
  - Implement context summarization
- [ ] Develop State Tracking
  - Create user state models
  - Implement progress tracking
  - Develop analytics systems

### Phase 5: Integration and Optimization
- [ ] Router Agent Implementation
  - Create agent coordination system
  - Implement request routing logic
  - Develop agent communication protocols
- [ ] System Optimization
  - Implement response caching
  - Optimize model performance
  - Reduce latency in agent switching

## Directory Structure
```
AI/
├── data/               # Training data and resources
│   ├── content/        # Structured content database
│   │   ├── mindfulness/    # Mindfulness and relaxation
│   │   ├── academic/       # Academic resources
│   │   ├── motivation/     # Motivational content
│   │   └── crisis/         # Crisis management
│   ├── recommendations/    # Recommendation templates
│   └── metadata/          # Content metadata
├── agents/            # Agent implementation modules
├── core/              # Core NLP and routing systems
├── memory/            # Memory management components
├── recommender/       # Recommendation engine
├── utils/             # Utility functions and helpers
└── config/            # Configuration files
```

## Development Guidelines

### Code Organization
- Use clear module separation for different agents
- Implement comprehensive logging
- Follow type hinting conventions
- Document all major functions and classes

### Testing Strategy
- Unit tests for individual agents
- Integration tests for agent interactions
- Conversation flow testing
- Performance benchmarking

### Data Management
- Maintain clear data versioning
- Implement data validation pipelines
- Regular backup of training data
- Clear documentation of data structures

## Implementation Notes

### Agent Communication
```python
# Example agent communication pattern
class AgentRouter:
    def route_request(self, user_input: str, context: Dict) -> Response:
        # Determine appropriate agent
        agent = self.select_agent(user_input, context)
        # Process request
        response = agent.process(user_input, context)
        # Update memory
        self.memory_manager.update(user_input, response, context)
        return response
```

### Memory Management
```python
# Example memory structure
class MemoryManager:
    def __init__(self):
        self.short_term = deque(maxlen=10)  # Recent interactions
        self.long_term = Database()         # Persistent storage
        self.context = {}                   # Current session context
```

## LangGraph Implementation Tutorial

### 1. Basic Setup

```python
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import Tool

# Define the state structure
class EmiliaState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_agent: str
    emotional_state: dict
    context: dict

# Initialize the graph
graph = StateGraph(EmiliaState)
```

### 2. Agent Implementation

```python
# Base agent setup with LLM
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

# Emotional Support Agent
def emotional_support_agent(state: EmiliaState):
    # Configure tools for content recommendation
    tools = [
        Tool(
            name="recommend_mindfulness",
            func=lambda q: get_mindfulness_content(state["emotional_state"]),
            description="Recommend mindfulness and relaxation content"
        ),
        Tool(
            name="recommend_motivation",
            func=lambda q: get_motivational_content(state["context"]),
            description="Recommend motivational content"
        )
    ]
    
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke(state["messages"])
    
    return {
        "messages": [response],
        "emotional_state": update_emotional_state(response)
    }

# Academic Planning Agent
def academic_planning_agent(state: EmiliaState):
    tools = [
        Tool(
            name="recommend_planning",
            func=lambda q: get_planning_resources(state["context"]),
            description="Recommend time management and planning resources"
        )
    ]
    
    llm_with_tools = llm.bind_tools(tools)
    return {"messages": [llm_with_tools.invoke(state["messages"])]}
```

### 3. Router Implementation

```python
def route_agents(state: EmiliaState):
    # Determine which agent should handle the request
    last_message = state["messages"][-1].content
    emotional_state = state["emotional_state"]
    
    if needs_emotional_support(last_message, emotional_state):
        return "emotional_support"
    elif needs_academic_planning(last_message):
        return "academic_planning"
    elif needs_crisis_management(last_message, emotional_state):
        return "crisis_management"
    else:
        return "general_chat"

# Add nodes to graph
graph.add_node("emotional_support", emotional_support_agent)
graph.add_node("academic_planning", academic_planning_agent)
graph.add_node("router", route_agents)

# Add edges
graph.add_conditional_edges(
    "router",
    {
        "emotional_support": lambda x: x == "emotional_support",
        "academic_planning": lambda x: x == "academic_planning",
        "crisis_management": lambda x: x == "crisis_management",
    }
)
```

### 4. Memory Management

```python
from collections import deque

class EmiliaMemoryManager:
    def __init__(self):
        self.short_term = deque(maxlen=10)
        self.long_term = {}
        self.context = {}
    
    def update_memory(self, state: EmiliaState):
        # Update conversation history
        self.short_term.append({
            "messages": state["messages"][-2:],  # Last interaction
            "emotional_state": state["emotional_state"],
            "agent": state["current_agent"]
        })
        
        # Update long-term memory if needed
        if significant_interaction(state):
            self.long_term[get_timestamp()] = {
                "interaction": state["messages"][-1],
                "emotional_state": state["emotional_state"],
                "recommendations": get_recommendations(state)
            }

# Add memory management to graph
def memory_node(state: EmiliaState):
    memory_manager.update_memory(state)
    return state

graph.add_node("memory", memory_node)
```

### 5. Content Recommendation Integration

```python
class ContentRecommender:
    def __init__(self):
        self.content_db = load_content_database()
    
    def recommend(self, state: EmiliaState) -> list:
        user_state = state["emotional_state"]
        context = state["context"]
        
        # Match content based on state and context
        relevant_content = self.content_db.query(
            emotional_state=user_state,
            context=context,
            limit=3
        )
        
        return format_recommendations(relevant_content)

# Add recommendation to graph
recommender = ContentRecommender()
def recommendation_node(state: EmiliaState):
    recommendations = recommender.recommend(state)
    return {
        **state,
        "recommendations": recommendations
    }

graph.add_node("recommender", recommendation_node)
```

### 6. Running the Graph

```python
# Compile the graph
chain = graph.compile()

# Initialize state
initial_state = {
    "messages": [],
    "current_agent": "router",
    "emotional_state": {"valence": 0, "arousal": 0},
    "context": {}
}

# Process user input
def process_user_input(user_message: str):
    state = initial_state.copy()
    state["messages"].append({
        "role": "user",
        "content": user_message
    })
    
    # Run the graph
    for event in chain.stream(state):
        if "messages" in event:
            # Handle response
            latest_message = event["messages"][-1]
            if latest_message.role == "assistant":
                print(f"Emilia: {latest_message.content}")
```

### Usage Example

```python
# Example usage
process_user_input("I'm feeling really stressed about my upcoming exams")
```

This implementation:
- Uses LangGraph's state management for tracking conversation and emotional state
- Implements specialized agents for different types of support
- Integrates content recommendations based on user state
- Maintains conversation memory and context
- Routes requests to appropriate agents based on user needs
- Provides structured responses with relevant recommendations

The graph flow:
1. User input → Router
2. Router → Specialized Agent
3. Agent → Memory Manager
4. Memory Manager → Content Recommender
5. Final response to user

Remember to handle errors appropriately and implement proper logging throughout the system.

## Development Timeline

1. **Week 1-2**: Core NLP Setup
   - LLM integration
   - Basic conversation handling

2. **Week 3-4**: Emotional Support Agent
   - Sentiment analysis
   - Response generation

3. **Week 5-6**: Academic Planning Agent
   - Task management
   - Schedule optimization

4. **Week 7-8**: Crisis Management Agent
   - Emergency protocols
   - Safety systems

5. **Week 9-10**: Memory System
   - Storage implementation
   - Retrieval mechanisms

6. **Week 11-12**: Integration
   - Router implementation
   - System optimization

## Dependencies

- Python 3.8+
- FastAPI
- LangChain
- PostgreSQL
- Redis (for caching)
- Transformers library

## Setup Instructions

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Contributing Guidelines

1. Create feature branches from `development`
2. Follow PEP 8 style guide
3. Include tests for new features
4. Update documentation as needed
5. Submit PR with clear description

## Monitoring and Evaluation

- Track response accuracy
- Monitor conversation quality
- Measure user satisfaction
- Log error rates and types
- Track performance metrics

## Security Considerations

- Implement data encryption
- Secure API endpoints
- Regular security audits
- Privacy compliance checks
- User data protection

## LangGraph Agent Implementation

The core chatbot functionality is implemented using LangGraph, providing a structured workflow with memory capabilities and specialized agents:

### Components

1. **State Management**
   - Conversation history tracking
   - Emotional state monitoring
   - Context preservation
   - Memory management

2. **Specialized Agents**
   - Emotional Support Agent
     - Empathetic responses
     - Coping strategies
     - Mindfulness exercises
   - Academic Planning Agent
     - Time management
     - Study scheduling
     - Task prioritization
   - Crisis Management Agent
     - Situation assessment
     - Immediate support
     - Professional referrals

3. **Router System**
   - Message analysis
   - Agent selection
   - Crisis detection
   - Context-aware routing

4. **Memory System**
   - Conversation history
   - Emotional state tracking
   - Interaction timestamps
   - Context preservation

### Usage

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
OPENROUTER_API_KEY=your_api_key_here
```

3. Run the chatbot:
```bash
python emilia_agent.py
``` 