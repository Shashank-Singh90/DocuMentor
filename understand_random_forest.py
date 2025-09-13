# 🎯 DAY 6: UNDERSTANDING RANDOM FOREST
# Let's understand YOUR project's ML algorithm step-by-step

import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

print("🌲 RANDOM FOREST EXPLAINED FOR CYBERSECURITY")
print("=" * 60)
print("Your IoT project uses Random Forest to detect threats!")
print("Let's understand WHY this works so well...\n")

# =============================================================================
# PART 1: ONE DECISION TREE (One Security Expert)
# =============================================================================

def single_expert_example():
    """Show how ONE security expert makes decisions"""
    print("👤 PART 1: ONE SECURITY EXPERT (Decision Tree)")
    print("-" * 50)
    
    print("Imagine Sarah, a cybersecurity expert, analyzing network traffic:")
    print()
    
    # Sarah's simple rules
    print("🧠 Sarah's Decision Rules:")
    print("   Rule 1: If packet_rate > 1000 packets/sec → THREAT")
    print("   Rule 2: Else if syn_ratio > 0.5 (50% SYN flags) → THREAT")  
    print("   Rule 3: Else → NORMAL")
    print()
    
    # Test Sarah's rules on some packets
    test_packets = [
        {"id": 1, "packet_rate": 1500, "syn_ratio": 0.3, "description": "High packet rate"},
        {"id": 2, "packet_rate": 500, "syn_ratio": 0.7, "description": "High SYN ratio"}, 
        {"id": 3, "packet_rate": 200, "syn_ratio": 0.1, "description": "Normal traffic"},
        {"id": 4, "packet_rate": 800, "syn_ratio": 0.6, "description": "Borderline case"}
    ]
    
    print("📊 Let's see Sarah analyze some packets:")
    print()
    
    for packet in test_packets:
        # Apply Sarah's rules
        if packet["packet_rate"] > 1000:
            decision = "THREAT (Rule 1: High packet rate)"
        elif packet["syn_ratio"] > 0.5:
            decision = "THREAT (Rule 2: High SYN ratio)"
        else:
            decision = "NORMAL (Rule 3: Default)"
        
        print(f"   Packet {packet['id']}: {packet['description']}")
        print(f"   Rate: {packet['packet_rate']}, SYN: {packet['syn_ratio']}")
        print(f"   🎯 Sarah's Decision: {decision}")
        print()
    
    print("❗ PROBLEM: What if Sarah makes mistakes?")
    print("   - Maybe 1000 is the wrong threshold?")
    print("   - What if she misses a sophisticated attack?")
    print("   - One expert = one point of failure!")
    print()
    input("Press Enter to see the solution...")

# =============================================================================
# PART 2: RANDOM FOREST (Team of Experts)
# =============================================================================

def team_of_experts_example():
    """Show how a TEAM of experts is more reliable"""
    print("\n👥 PART 2: TEAM OF SECURITY EXPERTS (Random Forest)")
    print("-" * 50)
    
    print("Solution: Get 5 different cybersecurity experts!")
    print("Each expert has different experience and focuses on different things.")
    print()
    
    # Create 5 different experts with different specialties
    experts = [
        {"name": "Sarah", "specialty": "packet_rate", "threshold": 1000, "focus": "Volume attacks"},
        {"name": "Mike", "specialty": "syn_ratio", "threshold": 0.4, "focus": "SYN flood attacks"},
        {"name": "Lisa", "specialty": "packet_size", "threshold": 100, "focus": "Small packet attacks"},
        {"name": "Dave", "specialty": "flow_duration", "threshold": 30, "focus": "Long connections"},
        {"name": "Amy", "specialty": "byte_rate", "threshold": 5000, "focus": "Data exfiltration"}
    ]
    
    print("🔍 Our Cybersecurity Team:")
    for expert in experts:
        print(f"   {expert['name']}: Specializes in {expert['focus']}")
    print()
    
    # Test packet for team analysis
    suspicious_packet = {
        "packet_rate": 800,      # Medium
        "syn_ratio": 0.6,        # High
        "packet_size": 80,       # Small
        "flow_duration": 45,     # Long
        "byte_rate": 6000        # High
    }
    
    print(f"📊 Analyzing suspicious packet:")
    for key, value in suspicious_packet.items():
        print(f"   {key}: {value}")
    print()
    
    # Each expert votes
    votes = []
    print("🗳️  Expert Voting:")
    
    for expert in experts:
        feature = expert["specialty"]
        threshold = expert["threshold"]
        packet_value = suspicious_packet.get(feature, 0)
        
        # Each expert applies their rule
        if expert["name"] in ["Sarah", "Amy"]:  # Higher values = threat
            vote = "THREAT" if packet_value > threshold else "NORMAL"
        elif expert["name"] == "Lisa":  # Lower values = threat
            vote = "THREAT" if packet_value < threshold else "NORMAL"
        else:  # Standard threshold
            vote = "THREAT" if packet_value > threshold else "NORMAL"
        
        votes.append(vote)
        print(f"   {expert['name']}: {vote} (looked at {feature}={packet_value})")
    
    # Final team decision
    threat_votes = votes.count("THREAT")
    normal_votes = votes.count("NORMAL")
    
    print(f"\n📊 TEAM VOTING RESULTS:")
    print(f"   🚨 THREAT votes: {threat_votes}")
    print(f"   ✅ NORMAL votes: {normal_votes}")
    print(f"   🎯 TEAM DECISION: {'THREAT' if threat_votes > normal_votes else 'NORMAL'}")
    print(f"   💪 Confidence: {max(threat_votes, normal_votes)/len(votes)*100:.1f}%")
    print()
    
    print("✅ ADVANTAGES of team voting:")
    print("   1. More reliable - one expert can't dominate")
    print("   2. Different perspectives catch different attacks")
    print("   3. Majority vote reduces false alarms")
    print("   4. More confident in decisions")
    print()
    
    input("Press Enter to see how this works in your actual project...")

# =============================================================================
# PART 3: YOUR ACTUAL PROJECT'S RANDOM FOREST
# =============================================================================

def your_project_random_forest():
    """Show how YOUR project implements this concept"""
    print("\n🎯 PART 3: YOUR IoT PROJECT'S RANDOM FOREST")
    print("-" * 50)
    
    print("Your project doesn't just use 5 experts...")
    print("It uses 100 EXPERTS (trees) voting on IoT threats!")
    print()
    
    # Simulate your project's features
    iot_features = [
        'flow_duration', 'Rate', 'syn_flag_number', 'rst_flag_number', 
        'Tot_size', 'fin_flag_number', 'ack_flag_number', 'packet_count',
        'byte_rate', 'syn_ratio', 'packet_ratio'
    ]
    
    print(f"🔍 Your project analyzes {len(iot_features)} different features:")
    for i, feature in enumerate(iot_features, 1):
        print(f"   {i:2}. {feature}")
    print()
    
    print("🌲 How your Random Forest works:")
    print("   1. Train 100 different decision trees")
    print("   2. Each tree focuses on different feature combinations")
    print("   3. Each tree learns different attack patterns")
    print("   4. When new IoT traffic arrives:")
    print("      - All 100 trees analyze it")
    print("      - Each tree votes: NORMAL or ATTACK")
    print("      - Majority vote wins")
    print("      - Your project reports 99.58% accuracy!")
    print()
    
    # Simulate a real prediction
    print("📡 EXAMPLE: Analyzing Real IoT Traffic")
    print("-" * 40)
    
    sample_traffic = {
        'flow_duration': 2.5,
        'Rate': 150.3,
        'syn_flag_number': 8,
        'rst_flag_number': 2,
        'Tot_size': 15420,
        'packet_count': 45,
        'syn_ratio': 0.18,
        'packet_ratio': 1.2
    }
    
    print("IoT device traffic sample:")
    for feature, value in sample_traffic.items():
        print(f"   {feature}: {value}")
    print()
    
    # Simulate 100 tree votes (simplified)
    np.random.seed(42)  # For consistent results
    tree_votes = []
    
    print("🗳️  Tree voting simulation (showing first 10 trees):")
    for i in range(10):
        # Each tree has slightly different logic
        vote = "NORMAL" if np.random.random() > 0.15 else "ATTACK"  # 85% vote normal
        tree_votes.append(vote)
        print(f"   Tree {i+1:2}: {vote}")
    
    # Simulate remaining 90 votes
    remaining_votes = ["NORMAL"] * 78 + ["ATTACK"] * 12  # 90 more votes
    tree_votes.extend(remaining_votes)
    
    normal_votes = tree_votes.count("NORMAL")
    attack_votes = tree_votes.count("ATTACK")
    
    print(f"   ... (90 more trees vote)")
    print()
    print(f"📊 FINAL VOTING RESULTS (100 trees):")
    print(f"   ✅ NORMAL: {normal_votes} votes")
    print(f"   🚨 ATTACK: {attack_votes} votes")
    print(f"   🎯 PREDICTION: {'NORMAL' if normal_votes > attack_votes else 'ATTACK'}")
    print(f"   🎪 CONFIDENCE: {max(normal_votes, attack_votes)}%")
    print()
    
    print("🏆 WHY YOUR PROJECT CHOSE RANDOM FOREST:")
    print("   ✅ HIGH ACCURACY: 99.58% on IoT threat detection")
    print("   ✅ INTERPRETABLE: Can explain which features matter")
    print("   ✅ FAST: Makes predictions in <100ms")
    print("   ✅ ROBUST: Doesn't overfit to training data")
    print("   ✅ HANDLES IMBALANCE: Good with rare attack samples")
    print()

# =============================================================================
# RUN THE COMPLETE LEARNING SESSION
# =============================================================================

if __name__ == "__main__":
    print("🎓 Welcome to Random Forest Learning Session!")
    print("We'll understand YOUR project's algorithm step by step.\n")
    
    # Part 1: Single expert
    single_expert_example()
    
    # Part 2: Team of experts  
    team_of_experts_example()
    
    # Part 3: Your actual project
    your_project_random_forest()
    
    print("\n🎯 CONGRATULATIONS!")
    print("You now understand Random Forest and why your project uses it!")
    print("Ready for the afternoon session: Training your own Random Forest!")
