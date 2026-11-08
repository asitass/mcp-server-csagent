#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客服智能体 MCP Server
把智能客服 Agent 的 5 个业务工具暴露为 MCP 标准服务。
数据为内存模拟（demo），生产环境替换为真实 DB/API 调用即可。
"""
import json
import random
import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("csagent")

# ---------- 模拟数据层（demo 用内存数据，生产替换为 DB/API） ----------
KB = {
    "退货政策": "收货后7天内可无理由退货，需保持商品完好；质量问题30天内免费退换，运费商家承担。",
    "发票开具": "电子发票在订单完成后24小时内自动开具，可在订单详情页下载；纸质发票需联系客服登记地址。",
    "配送时效": "现货商品48小时内发货，江浙沪皖次日达，全国3~5天；预售商品按页面标注时间发货。",
    "会员权益": "VIP会员享95折、每月2张免邮券、生日礼盒；PLUS会员额外享专属客服和延保服务。",
}
TICKETS = []
ORDERS = {
    "SO20261101001": {"user": "138****1234", "item": "无线降噪耳机", "status": "已发货", "carrier": "顺丰", "tracking": "SF1234567890"},
    "SO20261102088": {"user": "186****5678", "item": "机械键盘", "status": "待发货", "carrier": None, "tracking": None},
}
LOGS = [
    {"time": "2026-11-08 09:12:01", "level": "ERROR", "module": "payment", "msg": "支付回调超时, order=SO20261101001, retry=2"},
    {"time": "2026-11-08 09:13:44", "level": "WARN", "module": "inventory", "msg": "库存水位低于阈值 sku=KB-889, left=12"},
    {"time": "2026-11-08 10:02:17", "level": "INFO", "module": "chatbot", "msg": "agent工具调用 knowledge_search latency=210ms"},
    {"time": "2026-11-08 10:15:52", "level": "ERROR", "module": "logistics", "msg": "顺丰运单回传失败, tracking=SF1234567890"},
]

# ---------- 5 个业务工具（MCP 化） ----------

@mcp.tool()
def knowledge_search(query: str, category: str = "all") -> str:
    """知识库检索：按关键词检索客服知识库。query=检索关键词；category=分类过滤(all/售后/配送/会员/发票)"""
    hits = []
    for title, body in KB.items():
        if query in title or query in body:
            if category == "all" or category in title:
                hits.append({"title": title, "content": body})
    if not hits:
        return json.dumps({"hits": 0, "message": "知识库未命中, 建议转人工或创建工单", "query": query}, ensure_ascii=False)
    return json.dumps({"hits": len(hits), "results": hits}, ensure_ascii=False)

@mcp.tool()
def create_ticket(title: str, description: str, priority: str = "normal") -> str:
    """创建客服工单。title=标题; description=问题描述; priority=优先级(low/normal/high/urgent)"""
    if priority not in ("low", "normal", "high", "urgent"):
        return json.dumps({"ok": False, "error": f"非法优先级: {priority}"}, ensure_ascii=False)
    tid = f"TK{datetime.datetime.now():%Y%m%d}{random.randint(1000, 9999)}"
    ticket = {"id": tid, "title": title, "desc": description, "priority": priority,
              "status": "open", "created": datetime.datetime.now().isoformat(timespec="seconds")}
    TICKETS.append(ticket)
    return json.dumps({"ok": True, "ticket": ticket}, ensure_ascii=False)

@mcp.tool()
def query_order(order_id: str) -> str:
    """订单查询。order_id=订单号(SO开头)"""
    o = ORDERS.get(order_id)
    if not o:
        return json.dumps({"ok": False, "error": f"订单不存在: {order_id}"}, ensure_ascii=False)
    return json.dumps({"ok": True, "order_id": order_id, **o}, ensure_ascii=False)

@mcp.tool()
def query_logs(level: str = "ALL", keyword: str = "", last_n: int = 10) -> str:
    """服务日志查询。level=日志级别(ALL/INFO/WARN/ERROR); keyword=关键词过滤; last_n=返回条数上限"""
    rows = LOGS
    if level != "ALL":
        rows = [r for r in rows if r["level"] == level]
    if keyword:
        rows = [r for r in rows if keyword in r["msg"] or keyword in r["module"]]
    rows = rows[-last_n:]
    return json.dumps({"count": len(rows), "logs": rows}, ensure_ascii=False)

@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """发送通知邮件。to=收件人邮箱; subject=主题; body=正文"""
    if "@" not in to:
        return json.dumps({"ok": False, "error": f"非法邮箱: {to}"}, ensure_ascii=False)
    # demo: 生产环境替换为 SMTP/邮件 API 调用
    return json.dumps({"ok": True, "to": to, "subject": subject,
                       "message_id": f"<{random.randint(10**9, 10**10)}@csagent.demo>",
                       "note": "demo模式: 邮件未真实发出"}, ensure_ascii=False)

# ---------- 资源与提示词（MCP 扩展能力，加分项） ----------

@mcp.resource("csagent://kb/catalog")
def kb_catalog() -> str:
    """知识库目录（MCP resource, 供 client 拉取静态上下文）"""
    return json.dumps({k: v[:30] + "..." for k, v in KB.items()}, ensure_ascii=False)

@mcp.prompt()
def refund_flow(order_id: str) -> str:
    """退货流程引导提示词模板"""
    return f"""用户咨询订单 {order_id} 的退货问题。请按以下流程处理：
1. 先调用 query_order 确认订单状态
2. 调用 knowledge_search 检索"退货政策"
3. 根据政策判断是否符合退货条件，不符合则解释原因
4. 符合则调用 create_ticket 创建高优先级工单，并告知用户预计处理时长"""

if __name__ == "__main__":
    mcp.run()  # stdio 模式
