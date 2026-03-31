#!/usr/bin/env node
/**
 * Investment Advisor CLI (投资分析助手)
 * 数据源: Tushare API (通过Python脚本)
 * 
 * 用法:
 *   node scripts/analyze.mjs <symbol> [mode]
 * 
 * mode 参数:
 *   full         - 完整分析（技术面+基本面+综合建议）[默认]
 *   technical    - 仅技术面分析
 *   fundamental  - 仅基本面分析
 *   signal       - 交易信号
 *   portfolio    - 投资组合分析（symbol用逗号分隔多只股票）
 *   compare      - 股票对比（symbol用逗号分隔多只股票）
 * 
 * 示例:
 *   node scripts/analyze.mjs 600410 full
 *   node scripts/analyze.mjs 000001 technical
 *   node scripts/analyze.mjs 600410,000001,300750 portfolio
 * 
 * 输出: JSON 格式到 stdout
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 运行Python脚本并返回JSON
function runPython(scriptPath, args) {
    return new Promise((resolve, reject) => {
        const proc = spawn('python3', [scriptPath, ...args], {
            cwd: __dirname
        });
        
        let stdout = '';
        let stderr = '';
        
        proc.stdout.on('data', (data) => { stdout += data; });
        proc.stderr.on('data', (data) => { stderr += data; });
        
        proc.on('close', (code) => {
            if (code === 0) {
                try {
                    resolve(JSON.parse(stdout));
                } catch (e) {
                    reject(new Error(`JSON parse error: ${stdout}`));
                }
            } else {
                reject(new Error(stderr || `Exit code: ${code}`));
            }
        });
    });
}

async function analyzeTechnical(symbol, mode = 'full') {
    const scriptPath = join(__dirname, 'technical_tushare.py');
    return await runPython(scriptPath, [symbol, mode]);
}

async function analyzeFundamental(symbol, mode = 'full') {
    const scriptPath = join(__dirname, 'fundamental_tushare.py');
    return await runPython(scriptPath, [symbol, mode]);
}

function r(v) { return Math.round(v * 100) / 100; }

function calculateSentimentScore(quote, rsi) {
    let score = 50;
    
    if (quote && quote.pct_chg > 2) score += 10;
    else if (quote && quote.pct_chg < -2) score -= 10;
    
    if (rsi > 70) score -= 10;
    else if (rsi < 30) score += 10;
    else if (rsi >= 40 && rsi <= 60) score += 5;
    
    return Math.max(0, Math.min(100, score));
}

function determineRecommendation(overallScore, techScore, fundScore) {
    let grade;
    if (overallScore >= 85) grade = 'A+';
    else if (overallScore >= 80) grade = 'A';
    else if (overallScore >= 75) grade = 'A-';
    else if (overallScore >= 70) grade = 'B+';
    else if (overallScore >= 65) grade = 'B';
    else if (overallScore >= 60) grade = 'B-';
    else if (overallScore >= 55) grade = 'C+';
    else if (overallScore >= 50) grade = 'C';
    else if (overallScore >= 45) grade = 'C-';
    else if (overallScore >= 40) grade = 'D+';
    else if (overallScore >= 35) grade = 'D';
    else grade = 'D-';

    let recommendation;
    if (overallScore >= 80) recommendation = 'strong_buy';
    else if (overallScore >= 65) recommendation = 'buy';
    else if (overallScore >= 40) recommendation = 'hold';
    else if (overallScore >= 25) recommendation = 'sell';
    else recommendation = 'strong_sell';

    return { grade, recommendation };
}

function generateSignal(techData, fundData) {
    const signals = [];
    
    // RSI信号
    if (techData.rsi) {
        if (techData.rsi > 70) signals.push({ type: 'RSI', signal: 'overbought', strength: 'strong' });
        else if (techData.rsi < 30) signals.push({ type: 'RSI', signal: 'oversold', strength: 'strong' });
    }
    
    // MACD信号
    if (techData.macd) {
        if (techData.macd.macd > 0) signals.push({ type: 'MACD', signal: 'bullish', strength: 'moderate' });
        else if (techData.macd.macd < 0) signals.push({ type: 'MACD', signal: 'bearish', strength: 'moderate' });
    }
    
    // 趋势信号
    if (techData.trend) {
        signals.push({ type: 'Trend', signal: techData.trend, strength: 'strong' });
    }
    
    return signals;
}

async function analyzeSingle(symbol, mode = 'full') {
    const result = { symbol };
    
    try {
        // 技术面分析
        if (mode === 'technical' || mode === 'full' || mode === 'signal') {
            result.technical = await analyzeTechnical(symbol, 'technical');
        }
        
        // 基本面分析
        if (mode === 'fundamental' || mode === 'full' || mode === 'signal') {
            result.fundamental = await analyzeFundamental(symbol, 'fundamental');
        }
        
        // 综合评分和建议
        if (mode === 'full') {
            let techScore = 50;
            let fundScore = 50;
            
            // 技术面评分
            if (result.technical) {
                const tech = result.technical;
                if (tech.trend === 'bullish') techScore += 20;
                else if (tech.trend === 'bearish') techScore -= 20;
                
                if (tech.rsi) {
                    if (tech.rsi < 30) techScore += 15;
                    else if (tech.rsi > 70) techScore -= 15;
                }
                
                if (tech.macd && tech.macd.macd > 0) techScore += 10;
            }
            
            // 基本面评分
            if (result.fundamental && result.fundamental.financial) {
                const fin = result.fundamental.financial;
                if (fin.roe > 15) fundScore += 15;
                else if (fin.roe > 10) fundScore += 5;
                
                if (fin.netprofit_margin > 10) fundScore += 10;
                else if (fin.netprofit_margin > 5) fundScore += 5;
            }
            
            techScore = Math.max(0, Math.min(100, techScore));
            fundScore = Math.max(0, Math.min(100, fundScore));
            
            const overallScore = (techScore * 0.6 + fundScore * 0.4);
            
            result.scores = {
                technical: techScore,
                fundamental: fundScore,
                overall: r(overallScore)
            };
            
            const rec = determineRecommendation(overallScore, techScore, fundScore);
            result.recommendation = rec;
        }
        
        // 交易信号
        if (mode === 'signal') {
            result.signals = generateSignal(result.technical, result.fundamental);
        }
        
    } catch (error) {
        result.error = error.message;
    }
    
    return result;
}

async function main() {
    const args = process.argv.slice(2);
    const symbol = args[0];
    const mode = args[1] || 'full';
    
    if (!symbol) {
        console.error('Usage: node analyze.mjs <symbol> [mode]');
        console.error('Modes: full, technical, fundamental, signal');
        process.exit(1);
    }
    
    // 处理多只股票
    if (symbol.includes(',')) {
        const symbols = symbol.split(',');
        const results = await Promise.all(symbols.map(s => analyzeSingle(s.trim(), mode)));
        console.log(JSON.stringify(results, null, 2));
    } else {
        const result = await analyzeSingle(symbol, mode);
        console.log(JSON.stringify(result, null, 2));
    }
}

main().catch(console.error);
