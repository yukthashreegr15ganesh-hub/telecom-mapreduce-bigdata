#!/usr/bin/env python3
"""
Hadoop Streaming Reducer: Telecom Traffic Aggregation
Project: Large-Scale Telecommunication Data Processing and Performance Monitoring Using MapReduce

Aggregates mapper intermediate metrics by key and produces clean TSV output:
group_type
group_id
record_count
sms_in_sum, sms_in_cnt, sms_in_avg
sms_out_sum, sms_out_cnt, sms_out_avg
call_in_sum, call_in_cnt, call_in_avg
call_out_sum, call_out_cnt, call_out_avg
internet_sum, internet_cnt, internet_avg
total_traffic_sum
"""

import sys

def emit_result(current_key, acc):
    # current_key: e.g. CELL_1, TIME_1383260400000, COUNTRY_39
    if "_" not in current_key:
        return
    group_type, group_id = current_key.split("_", 1)

    rec_cnt = acc[0]
    s_in_sum, s_in_cnt = acc[1], acc[2]
    s_out_sum, s_out_cnt = acc[3], acc[4]
    c_in_sum, c_in_cnt = acc[5], acc[6]
    c_out_sum, c_out_cnt = acc[7], acc[8]
    net_sum, net_cnt = acc[9], acc[10]

    s_in_avg = (s_in_sum / s_in_cnt) if s_in_cnt > 0 else 0.0
    s_out_avg = (s_out_sum / s_out_cnt) if s_out_cnt > 0 else 0.0
    c_in_avg = (c_in_sum / c_in_cnt) if c_in_cnt > 0 else 0.0
    c_out_avg = (c_out_sum / c_out_cnt) if c_out_cnt > 0 else 0.0
    net_avg = (net_sum / net_cnt) if net_cnt > 0 else 0.0

    total_traffic = s_in_sum + s_out_sum + c_in_sum + c_out_sum + net_sum

    row = [
        group_type,
        group_id,
        str(rec_cnt),
        f"{s_in_sum:.6f}", str(s_in_cnt), f"{s_in_avg:.6f}",
        f"{s_out_sum:.6f}", str(s_out_cnt), f"{s_out_avg:.6f}",
        f"{c_in_sum:.6f}", str(c_in_cnt), f"{c_in_avg:.6f}",
        f"{c_out_sum:.6f}", str(c_out_cnt), f"{c_out_avg:.6f}",
        f"{net_sum:.6f}", str(net_cnt), f"{net_avg:.6f}",
        f"{total_traffic:.6f}"
    ]
    sys.stdout.write("\t".join(row) + "\n")

def main():
    current_key = None
    # [rec_cnt, s_in_sum, s_in_cnt, s_out_sum, s_out_cnt, c_in_sum, c_in_cnt, c_out_sum, c_out_cnt, net_sum, net_cnt]
    acc = [0, 0.0, 0, 0.0, 0, 0.0, 0, 0.0, 0, 0.0, 0]

    for line in sys.stdin:
        line = line.rstrip("\r\n")
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 12:
            continue

        key = parts[0]
        try:
            cnt = int(parts[1])
            s_in_s = float(parts[2])
            s_in_c = int(parts[3])
            s_out_s = float(parts[4])
            s_out_c = int(parts[5])
            c_in_s = float(parts[6])
            c_in_c = int(parts[7])
            c_out_s = float(parts[8])
            c_out_c = int(parts[9])
            net_s = float(parts[10])
            net_c = int(parts[11])
        except ValueError:
            continue

        if current_key == key:
            acc[0] += cnt
            acc[1] += s_in_s
            acc[2] += s_in_c
            acc[3] += s_out_s
            acc[4] += s_out_c
            acc[5] += c_in_s
            acc[6] += c_in_c
            acc[7] += c_out_s
            acc[8] += c_out_c
            acc[9] += net_s
            acc[10] += net_c
        else:
            if current_key is not None:
                emit_result(current_key, acc)
            current_key = key
            acc = [cnt, s_in_s, s_in_c, s_out_s, s_out_c, c_in_s, c_in_c, c_out_s, c_out_c, net_s, net_c]

    if current_key is not None:
        emit_result(current_key, acc)

if __name__ == "__main__":
    main()
