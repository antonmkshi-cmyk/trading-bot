# обавляем в recovery_manager.py метод для умного отсева

def should_switch_strategy(self, coin, strategy_name, trade_history):
    """ешение о смене стратегии на основе статистики, а не одной сделки"""
    stats = self.get_strategy_stats(coin, strategy_name, trade_history)
    
    # сли стратегия дала 3 убытка из последних 5 сделок
    if stats['recent_loss_rate'] >= 0.6:
        logger.info(f"[RECOVERY] {coin}: {strategy_name} has {stats['recent_loss_rate']*100:.0f}% loss rate (3/5), switching")
        return True
    
    # сли общий winrate стратегии ниже 35% за 20+ сделок
    if stats['total_trades'] >= 20 and stats['winrate'] < 0.35:
        logger.info(f"[RECOVERY] {coin}: {strategy_name} winrate {stats['winrate']*100:.0f}% below 35%, switching")
        return True
    
    return False

def get_strategy_stats(self, coin, strategy_name, trade_history):
    """Собирает статистику по стратегии"""
    relevant_trades = [t for t in trade_history if t.get('strategy') == strategy_name]
    recent = relevant_trades[-5:] if len(relevant_trades) >= 5 else relevant_trades
    
    recent_losses = len([t for t in recent if t.get('pnl', 0) < 0])
    recent_loss_rate = recent_losses / len(recent) if recent else 0
    
    wins = len([t for t in relevant_trades if t.get('pnl', 0) > 0])
    total = len(relevant_trades)
    winrate = wins / total if total > 0 else 0.5
    
    return {
        'recent_loss_rate': recent_loss_rate,
        'winrate': winrate,
        'total_trades': total,
        'recent_trades': len(recent)
    }
