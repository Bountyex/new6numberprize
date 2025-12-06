import pandas as pd
import numpy as np
import time, heapq
from itertools import combinations
import streamlit as st

st.title("⚡ Ultra-Fast 6 Number Lowest Payout Optimizer (NumPy Turbo Engine)")

uploaded = st.file_uploader("Upload Excel file", type=["xlsx"])
if uploaded:
    df = pd.read_excel(uploaded)

    # Detect numbers column
    candidates = [c for c in df.columns if ("selected" in str(c).lower()) or ("number" in str(c).lower())]
    num_col = candidates[0] if candidates else df.columns[0]
    st.write(f"Detected numbers column: `{num_col}`")

    # --- Ticket parser ---
    def parse_ticket(s):
        if pd.isna(s):
            return []
        s = str(s).replace(";", ",")
        nums = []
        for p in s.split(","):
            p = p.strip()
            if p.isdigit():
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

    # --- Convert tickets to bitmasks ---
    # 25 bits -> fits in uint32
    bitmasks = np.zeros(T, dtype=np.uint32)
    for i, t in enumerate(tickets):
        mask = 0
        for n in t:
            if 1 <= n <= 25:
                mask |= (1 << (n - 1))
        bitmasks[i] = mask

    st.subheader("💰 Dynamic Prize Settings")
    prize_3 = st.number_input("Prize for 3 matches", min_value=0, value=15)
    prize_4 = st.number_input("Prize for 4 matches", min_value=0, value=400)
    prize_5 = st.number_input("Prize for 5 matches", min_value=0, value=1850)
    prize_6 = st.number_input("Prize for 6 matches", min_value=0, value=50000)

    payout_map = np.zeros(7, dtype=np.int32)
    payout_map[3] = prize_3
    payout_map[4] = prize_4
    payout_map[5] = prize_5
    payout_map[6] = prize_6

    top_n = st.slider("How many unique payout combos to show?", 5, 50, 10)

    if st.button("🚀 Start Optimization (Turbo Mode)"):

        start = time.time()

        all_combos = list(combinations(range(25), 6))

        best_heap = []
        seen_totals = set()

        # Pre-define NumPy lookup for bit-count (0–25)
        bitcount = np.array([bin(i).count("1") for i in range(1 << 6)], dtype=np.uint8)

        for combo in all_combos:

            # Build bitmask for this 6-number guess
            c_mask = 0
            for idx in combo:
                c_mask |= (1 << idx)

            # Vectorized match count: count of bits from c_mask inside ticket bitmasks
            overlap = (bitmasks & c_mask)

            # Extract exactly the bits from combo (0–6 bits)
            # Equivalent to popcount, but much faster through table lookup.
            x = overlap >> 0  # keep as uint32
            x = ((x >> 0) & 1) + ((x >> 1) & 1) + ((x >> 2) & 1) + ((x >> 3) & 1) + ((x >> 4) & 1) + ((x >> 5) & 1)

            # Now x = match count for each ticket (0–6)
            counts = np.bincount(x, minlength=7)

            # Compute payout
            total = int((counts * payout_map).sum())

            # Unique payout only
            if total in seen_totals:
                continue

            item = (total, tuple(i+1 for i in combo))

            if len(best_heap) < top_n:
                heapq.heappush(best_heap, (-total, item))
                seen_totals.add(total)

            else:
                if total < -best_heap[0][0]:
                    removed = -best_heap[0][0]
                    heapq.heapreplace(best_heap, (-total, item))
                    seen_totals.discard(removed)
                    seen_totals.add(total)

        best_list = [i[1] for i in sorted(best_heap, key=lambda x: x[1][0])]

        results = pd.DataFrame([
            {"Rank": r+1, "Combination": ",".join(map(str, combo)), "Total_Payout": total}
            for r, (total, combo) in enumerate(best_list)
        ])

        st.success(f"Completed in {time.time() - start:.2f} seconds! ⚡")
        st.dataframe(results)
