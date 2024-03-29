# FTX 期限套利機器人

1. 僅使用可做為保證金之貨幣，以便後續建立槓桿

2. 期現市場選取策略
    - 期限價差（spread）取絕對值後當作排序依據 -> 越大對於開倉越有利
    - 資金費率（funding rate）取絕對值後當作排序依據 -> 越大對於預期收益越有利
    - 距離下一次領取資金費率的時間 t 當作排序依據 -> 越小表示預估的 funding rate 越不可靠
    - 持有比例佔總資產 n % 以上時忽略該貨幣

3. 掛單策略
    - 皆使用市價掛單
    - 以期現市場共同最小單位為一掛單單位
    - 根據目前槓桿倍數與期望槓桿倍數之落差，調整掛單單位至數個整數倍
    - 當預估資金費率為正時，現貨做多，期貨做空；當預估資金費率為負時，現貨做空，期貨做多

4. 定期檢查持倉
    - 槓桿過低時加倉，槓桿過高時減倉
    - 期貨倉位與現貨餘額不一致時補倉
    - 資金費率虧錢時減倉

5. 出場策略（獲利了結）
    - 定期定額從子帳戶提取 USD/USDT 至其他帳戶（可避免因關閉子帳戶內的交易對而造成額外手續費）

- 注意特殊狀況
    - 不操作反向交易對（現貨做空，期貨做多）
    - spread < 0 才減倉；spread 很高時，即使已經達到目標 leverage 也要加倉（spread 的效益 > 資金費率的效益）
    - FTT 可降低手續費，應列入白名單，為必選之交易對
    - 改用 websocket 接收市價，以便計算 spread rate
    - 手續費計算：
        完成一次套利所需手續費 = taker 單筆交易 `0.07%` 手續費 * `2`（交易對同時有買單與賣單） * `2`（完成一次開倉關倉循環）
                             = `0.28%`
        即開關倉時 spread rate 差異至少要大於 0.28% 才能 0 成本攤平手續費
        實務上，自拿到 spread rate 至完成交易會有時間差，這段期間市場可能已產生變化，因此需要預留緩衝空間，例如乘以 1.2 倍：
        0.28% * 1.2 = 0.336%
        則可以在 spread rate > 0.336% 時建倉； spread rate < 0% 時關倉，全倉完成一輪開關倉循環時應當自動攤平交易手續費
    - 紀錄實際購買到的 spread rate
    - coin whitelist & blacklist
