import sys
from engine.context_store import store
from engine.conversation_manager import conversation_manager

store.teardown()

# Test runner
results = []

# Test 1: COMMIT
res1 = conversation_manager.handle_reply(
    conversation_id="test_conv_1",
    merchant_id="m_007_powerhouse_gym_bangalore",
    customer_id=None,
    from_role="merchant",
    message="Yes, go ahead",
    turn_number=1
)
t1_pass = res1.get("intent") == "COMMIT"
results.append(("Test 1: 'Yes, go ahead'", "COMMIT", res1.get("intent"), res1.get("body"), t1_pass))

# Test 2: Multi-turn COMMIT followed by NO_CHANGE
conv_id_2 = "test_conv_2"
res2_a = conversation_manager.handle_reply(
    conversation_id=conv_id_2,
    merchant_id="m_007_powerhouse_gym_bangalore",
    customer_id=None,
    from_role="merchant",
    message="Yes, go ahead",
    turn_number=1
)
res2_b = conversation_manager.handle_reply(
    conversation_id=conv_id_2,
    merchant_id="m_007_powerhouse_gym_bangalore",
    customer_id=None,
    from_role="merchant",
    message="no change i need",
    turn_number=2
)
t2_pass = (res2_b.get("intent") == "NO_CHANGE") and (res2_b.get("body") != res2_a.get("body"))
results.append(("Test 2: Turn 2 'no change i need'", "NO_CHANGE", res2_b.get("intent"), res2_b.get("body"), t2_pass))

# Test 3: MODIFY
res3 = conversation_manager.handle_reply(
    conversation_id="test_conv_3",
    merchant_id="m_007_powerhouse_gym_bangalore",
    customer_id=None,
    from_role="merchant",
    message="Change the headline",
    turn_number=1
)
t3_pass = res3.get("intent") == "MODIFY"
results.append(("Test 3: 'Change the headline'", "MODIFY", res3.get("intent"), res3.get("body"), t3_pass))

# Test 4: HOSTILE
res4 = conversation_manager.handle_reply(
    conversation_id="test_conv_4",
    merchant_id="m_007_powerhouse_gym_bangalore",
    customer_id=None,
    from_role="merchant",
    message="Stop messaging me",
    turn_number=1
)
t4_pass = res4.get("intent") == "HOSTILE" and res4.get("action") == "end"
results.append(("Test 4: 'Stop messaging me'", "HOSTILE", res4.get("intent"), res4.get("body"), t4_pass))

# Test 5: OUT_OF_SCOPE
res5 = conversation_manager.handle_reply(
    conversation_id="test_conv_5",
    merchant_id="m_007_powerhouse_gym_bangalore",
    customer_id=None,
    from_role="merchant",
    message="Can you file my GST return?",
    turn_number=1
)
t5_pass = res5.get("intent") == "OUT_OF_SCOPE"
results.append(("Test 5: 'Can you file my GST return?'", "OUT_OF_SCOPE", res5.get("intent"), res5.get("body"), t5_pass))

# Test 6: QUESTION
res6 = conversation_manager.handle_reply(
    conversation_id="test_conv_6",
    merchant_id="m_007_powerhouse_gym_bangalore",
    customer_id=None,
    from_role="merchant",
    message="How did you calculate the 30% drop?",
    turn_number=1
)
t6_pass = res6.get("intent") == "QUESTION"
results.append(("Test 6: 'How did you calculate the 30% drop?'", "QUESTION", res6.get("intent"), res6.get("body"), t6_pass))

# Test 7: REJECT
res7 = conversation_manager.handle_reply(
    conversation_id="test_conv_7",
    merchant_id="m_007_powerhouse_gym_bangalore",
    customer_id=None,
    from_role="merchant",
    message="Don't proceed",
    turn_number=1
)
t7_pass = res7.get("intent") == "REJECT" and res7.get("action") == "end"
results.append(("Test 7: 'Don\'t proceed'", "REJECT", res7.get("intent"), res7.get("body"), t7_pass))

# Test 8: NO_CHANGE
res8 = conversation_manager.handle_reply(
    conversation_id="test_conv_8",
    merchant_id="m_007_powerhouse_gym_bangalore",
    customer_id=None,
    from_role="merchant",
    message="Keep everything as it is",
    turn_number=1
)
t8_pass = res8.get("intent") == "NO_CHANGE"
results.append(("Test 8: 'Keep everything as it is'", "NO_CHANGE", res8.get("intent"), res8.get("body"), t8_pass))

# Test 9: COMMIT
res9 = conversation_manager.handle_reply(
    conversation_id="test_conv_9",
    merchant_id="m_007_powerhouse_gym_bangalore",
    customer_id=None,
    from_role="merchant",
    message="Do it",
    turn_number=1
)
t9_pass = res9.get("intent") == "COMMIT"
results.append(("Test 9: 'Do it'", "COMMIT", res9.get("intent"), res9.get("body"), t9_pass))

# Test 10: AMBIGUOUS
res10 = conversation_manager.handle_reply(
    conversation_id="test_conv_10",
    merchant_id="m_007_powerhouse_gym_bangalore",
    customer_id=None,
    from_role="merchant",
    message="Maybe, I'll think about it",
    turn_number=1
)
t10_pass = res10.get("intent") == "AMBIGUOUS"
results.append(("Test 10: 'Maybe, I\'ll think about it'", "AMBIGUOUS", res10.get("intent"), res10.get("body"), t10_pass))

print("\n" + "="*80)
print(f"{'TEST CASE':<38} | {'EXPECTED':<12} | {'ACTUAL':<12} | {'STATUS'}")
print("="*80)
all_pass = True
for name, exp, act, body, passed in results:
    status_str = "PASSED [OK]" if passed else "FAILED [X]"
    if not passed: all_pass = False
    print(f"{name:<38} | {exp:<12} | {act:<12} | {status_str}")
    print(f"   -> Vera reply: {body}\n")
print("="*80)
print("ALL 10 TESTS PASSED!" if all_pass else "SOME TESTS FAILED!")
sys.exit(0 if all_pass else 1)
