#!/usr/bin/env python3
"""
Hadoop Streaming Mapper: Telecom Traffic Aggregation
Project: Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce

Input Schema:
0: cell_id
1: timestamp
2: country_code
3: sms_in
4: sms_out
5: call_in
6: call_out
7: internet_traffic

Emits grouped metrics for:
- CELL_<cell_id>
- TIME_<timestamp>
- COUNTRY_<country_code>

Metrics:
count, sms_in_sum, sms_in_cnt, sms_out_sum, sms_out_cnt,
call_in_sum, call_in_cnt, call_out_sum, call_out_cnt, internet_sum, internet_cnt
"""

import sys

FLUSH_INTERVAL = 250000

def flush_table(table):
    for key, vals in table.items():
        # vals: [count, s_in_sum, s_in_cnt, s_out_sum, s_out_cnt, c_in_sum, c_in_cnt, c_out_sum, c_out_cnt, net_sum, net_cnt]
        val_str = "\t".join(f"{v:.8g}" if isinstance(v, float) else str(v) for v in vals)
        sys.stdout.write(f"{key}\t{val_str}\n")
    table.clear()

def main():
    table = {}
    lines_since_flush = 0

    for line in sys.stdin:
        line = line.rstrip("\r\n")
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 8:
            continue

        try:
            cell_id = parts[0]
            timestamp = parts[1]
            country_code = parts[2]

            # Validate basic types
            int(cell_id)
            int(timestamp)
            int(country_code)
        except ValueError:
            continue

        # Parse traffic fields
        # (val, count)
        traffic_data = []
        for i in range(3, 8):
            f_str = parts[i].strip()
            if f_str == "":
                traffic_data.append((0.0, 0))
            else:
                try:
                    v = float(f_str)
                    if v >= 0.0:
                        traffic_data.append((v, 1))
                    else:
                        traffic_data.append((0.0, 0))
                except ValueError:
                    traffic_data.append((0.0, 0))

        s_in_v, s_in_c = traffic_data[0]
        s_out_v, s_out_c = traffic_data[1]
        c_in_v, c_in_c = traffic_data[2]
        c_out_v, c_out_c = traffic_data[3]
        net_v, net_c = traffic_data[4]

        keys = (
            f"CELL_{cell_id}",
            f"TIME_{timestamp}",
            f"COUNTRY_{country_code}"
        )

        for k in keys:
            if k not in table:
                table[k] = [1, s_in_v, s_in_c, s_out_v, s_out_c, c_in_v, c_in_c, c_out_v, c_out_c, net_v, net_c]
            else:
                acc = table[k]
                acc[0] += 1
                acc[1] += s_in_v
                acc[2] += s_in_c
                acc[3] += s_out_v
                acc[4] += s_out_c
                acc[5] += c_in_v
                acc[6] += c_in_c
                acc[7] += c_out_v
                acc[8] += c_out_c
                acc[9] += net_v
                acc[10] += net_c

        lines_since_flush += 1
        if lines_since_flush >= FLUSH_INTERVAL:
            flush_table(table)
            lines_since_flush = 0

    if table:
        flush_table(table)

if __name__ == "__main__":
    main()
