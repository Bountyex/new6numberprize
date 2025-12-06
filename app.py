import pandas as pd
import numpy as np
import time, math, heapq
from itertools import combinations
import streamlit as st

st.title("⚡️ 6 Number Lowest Payout Optimizer (Dynamic Prize Amounts)")

uploaded = st.file_uploader("Upload Excel file", type=["xlsx"])
if uploaded:
    df = pd.read_excel(uploaded)

    # --- Detect number column ---
    candidates = [c for c in df.columns if ("selected" in str(c).lower()) or ("number" in str(c).lower())]
    num_col = candidates[0] if candidates else df.columns[0]
    st.write(f"Detected numbers column: `{num_col}`")

    # --- Ticket parser ---
    def parse_ticket(s):
        if pd.isna(s): 
            return []
        s = str(s).replace(";", ",")
        parts = [p.strip() for p in s.split(",") if p.strip() != ""]
        nums = []
        for p in parts:
            if " " in p and not p.isdigit():
                sub = [q for q in p.split() if q.strip().isdigit()]
                nums.extend([int(q) for q in sub])
            elif p.isdigit():
                nums.append(int(p))
            else:
                try:
                    nums.append(int("".join(ch for ch in p if ch.isdigit())))
                except:
                    pass
        return list(dict.fromkeys(nums))

    tickets = [parse_ticket(x) for x in df[num_col].tolist()]
    T = len(tickets)
    st.write(f"Loaded {T} tickets.")

    # --- Build presence matrix ---
    presence = np.zeros((25, T), dtype=np.uint8)
    for j, t in enumerate(tickets):
        for n in t:
            if 1 <= n <= 25:
                presence[n-1, j] = 1

    st.subheader("💰 Dynamic Prize Settings")

    # --- User Editable Prize Amounts ---
    prize_3 = st.number_input("Prize for 3 matches", min_value=0, value=15)
    prize_4 = st.number_input("Prize for 4 matches", min_value=0, value=400)
    prize_5 = st.number_input("Prize for 5 matches", min_value=0, value=1850)
    prize_6 = st.number_input("Prize for 6 matches", min_value=0, value=50000)

    payout_map = np.zeros(7, dtype=np.int64)
    payout_map[3] = prize_3
    payout_map[4] = prize_4
    payout_map[5] = prize_5
    payout_map[6] = prize_6

    # --- Optimization Settings ---
    top_n = st.slider("How many top combos to display?", 5, 20, 10)

    if st.button("🔍 Start Optimization"):
        all_combos = list(combinations(range(25), 6))
        best_heap = []

        start = time.time()

        for combo in all_combos:
            matches = presence[list(combo), :].sum(axis=0).astype(np.int64)
            counts = np.bincount(matches, minlength=7)
            total = int((counts * payout_map).sum())

            item = (total, tuple(i+1 for i in combo))

            if len(best_heap) < top_n:
                heapq.heappush(best_heap, (-total, item))
            else:
                if total < -best_heap[0][0]:
                    heapq.heapreplace(best_heap, (-total, item))

        best_list = [i[1] for i in sorted(best_heap, key=lambda x: x[1][0])]
        results = pd.DataFrame([{
            "Rank": r+1,
            "Combination": ",".join(map(str, combo)),
            "Total_Payout": total
        } for r, (total, combo) in enumerate(best_list)])

        st.success("Optimization complete!")
        st.dataframe(results)
