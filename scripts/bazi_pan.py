#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八字排盘工具 v1.0.0
天工长老开发

功能：四柱八字排盘、十神计算、大运排法、基础断语
v1.0.0 基础版：四柱排盘、十神显示、大运计算
"""

import argparse
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ============== 基础数据 ==============

# 十天干
TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']

# 十二地支
DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 天干五行
GAN_WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'
}

# 地支五行
ZHI_WUXING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
    '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'
}

# 天干阴阳
GAN_YIN_YANG = {
    '甲': '阳', '乙': '阴', '丙': '阳', '丁': '阴', '戊': '阳',
    '己': '阴', '庚': '阳', '辛': '阴', '壬': '阳', '癸': '阴'
}

# 地支阴阳
ZHI_YIN_YANG = {
    '子': '阳', '丑': '阴', '寅': '阳', '卯': '阴', '辰': '阳', '巳': '阴',
    '午': '阳', '未': '阴', '申': '阳', '酉': '阴', '戌': '阳', '亥': '阴'
}

# 地支藏干（简化版）
ZHI_CANG_GAN = {
    '子': ['癸'],
    '丑': ['己', '癸', '辛'],
    '寅': ['甲', '丙', '戊'],
    '卯': ['乙'],
    '辰': ['戊', '乙', '癸'],
    '巳': ['丙', '戊', '庚'],
    '午': ['丁', '己'],
    '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'],
    '酉': ['辛'],
    '戌': ['戊', '辛', '丁'],
    '亥': ['壬', '甲'],
}

# 十神
SHI_SHEN = {
    '比肩': '同我者，阴阳同',
    '劫财': '同我者，阴阳异',
    '食神': '我生者，阴阳同',
    '伤官': '我生者，阴阳异',
    '偏财': '我克者，阴阳同',
    '正财': '我克者，阴阳异',
    '七杀': '克我者，阴阳同',
    '正官': '克我者，阴阳异',
    '偏印': '生我者，阴阳同',
    '正印': '生我者，阴阳异',
}

# 六十甲子（用于日柱查询）
LIU_SHI_JIA_ZI = [
    '甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳', '庚午', '辛未', '壬申', '癸酉',
    '甲戌', '乙亥', '丙子', '丁丑', '戊寅', '己卯', '庚辰', '辛巳', '壬午', '癸未',
    '甲申', '乙酉', '丙戌', '丁亥', '戊子', '己丑', '庚寅', '辛卯', '壬辰', '癸巳',
    '甲午', '乙未', '丙申', '丁酉', '戊戌', '己亥', '庚子', '辛丑', '壬寅', '癸卯',
    '甲辰', '乙巳', '丙午', '丁未', '戊申', '己酉', '庚戌', '辛亥', '壬子', '癸丑',
    '甲寅', '乙卯', '丙辰', '丁巳', '戊午', '己未', '庚申', '辛酉', '壬戌', '癸亥',
]

# 节气数据（简化版，用于月柱计算）
JIE_QI = {
    1: ('小寒', '大寒'),
    2: ('立春', '雨水'),
    3: ('惊蛰', '春分'),
    4: ('清明', '谷雨'),
    5: ('立夏', '小满'),
    6: ('芒种', '夏至'),
    7: ('小暑', '大暑'),
    8: ('立秋', '处暑'),
    9: ('白露', '秋分'),
    10: ('寒露', '霜降'),
    11: ('立冬', '小雪'),
    12: ('大雪', '冬至'),
}


class BaZiPan:
    """八字排盘类"""
    
    @classmethod
    def get_year_gan_zhi(cls, year: int) -> Tuple[str, str]:
        """获取年柱干支"""
        # 以立春为界，简化处理：2 月 4 日前算上一年
        gan_index = (year - 4) % 10
        zhi_index = (year - 4) % 12
        return TIAN_GAN[gan_index], DI_ZHI[zhi_index]
    
    @classmethod
    def get_month_gan_zhi(cls, year: int, month: int, day: int) -> Tuple[str, str]:
        """获取月柱干支"""
        # 月支固定（寅月=正月）
        month_zhi_index = (month + 2) % 12
        if month_zhi_index == 0:
            month_zhi_index = 12
        month_zhi = DI_ZHI[month_zhi_index - 1]
        
        # 月干：五虎遁
        year_gan, _ = cls.get_year_gan_zhi(year)
        year_gan_index = TIAN_GAN.index(year_gan)
        
        # 甲己→丙寅，乙庚→戊寅，丙辛→庚寅，丁壬→壬寅，戊癸→甲寅
        start_gan_map = {0: 2, 1: 4, 2: 6, 3: 8, 4: 0, 5: 2, 6: 4, 7: 6, 8: 8, 9: 0}
        start_gan_index = start_gan_map.get(year_gan_index, 2)
        
        month_gan_index = (start_gan_index + month - 1) % 10
        month_gan = TIAN_GAN[month_gan_index]
        
        return month_gan, month_zhi
    
    @classmethod
    def get_day_gan_zhi(cls, year: int, month: int, day: int) -> Tuple[str, str]:
        """获取日柱干支（简化算法）"""
        # 使用蔡勒公式计算日柱
        # 基准日：1900 年 1 月 31 日 = 甲戌日（索引 10）
        base_date = datetime(1900, 1, 31)
        target_date = datetime(year, month, day)
        delta_days = (target_date - base_date).days
        
        # 60 甲子循环
        jia_zi_index = (10 + delta_days) % 60
        if jia_zi_index < 0:
            jia_zi_index += 60
        
        gan_zhi = LIU_SHI_JIA_ZI[jia_zi_index]
        return gan_zhi[0], gan_zhi[1]
    
    @classmethod
    def get_hour_gan_zhi(cls, day_gan: str, hour: int) -> Tuple[str, str]:
        """获取时柱干支"""
        # 时支：23-1=子，1-3=丑，以此类推
        hour_zhi_index = ((hour + 1) % 24) // 2
        hour_zhi = DI_ZHI[hour_zhi_index]
        
        # 时干：五鼠遁
        day_gan_index = TIAN_GAN.index(day_gan)
        
        # 甲己→甲子，乙庚→丙子，丙辛→戊子，丁壬→庚子，戊癸→壬子
        start_gan_map = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8, 5: 0, 6: 2, 7: 4, 8: 6, 9: 8}
        start_gan_index = start_gan_map.get(day_gan_index, 0)
        
        hour_gan_index = (start_gan_index + hour_zhi_index) % 10
        hour_gan = TIAN_GAN[hour_gan_index]
        
        return hour_gan, hour_zhi
    
    @classmethod
    def get_shi_shen(cls, day_gan: str, other_gan: str) -> str:
        """根据日干计算十神"""
        day_wuxing = GAN_WUXING[day_gan]
        day_yin_yang = GAN_YIN_YANG[day_gan]
        
        other_wuxing = GAN_WUXING[other_gan]
        other_yin_yang = GAN_YIN_YANG[other_gan]
        
        # 判断关系
        if day_wuxing == other_wuxing:
            # 同我者
            if day_yin_yang == other_yin_yang:
                return '比肩'
            else:
                return '劫财'
        
        # 我生者
        wuxing_sheng = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
        if wuxing_sheng.get(day_wuxing) == other_wuxing:
            if day_yin_yang == other_yin_yang:
                return '食神'
            else:
                return '伤官'
        
        # 我克者
        wuxing_ke = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
        if wuxing_ke.get(day_wuxing) == other_wuxing:
            if day_yin_yang == other_yin_yang:
                return '偏财'
            else:
                return '正财'
        
        # 克我者
        reverse_ke = {'土': '木', '金': '火', '水': '土', '木': '金', '火': '水'}
        if reverse_ke.get(day_wuxing) == other_wuxing:
            if day_yin_yang == other_yin_yang:
                return '七杀'
            else:
                return '正官'
        
        # 生我者
        reverse_sheng = {'火': '木', '土': '火', '金': '土', '水': '金', '木': '水'}
        if reverse_sheng.get(day_wuxing) == other_wuxing:
            if day_yin_yang == other_yin_yang:
                return '偏印'
            else:
                return '正印'
        
        return '未知'
    
    @classmethod
    def get_da_yun(cls, year: int, month: int, day: int, hour: int, gender: str = '男') -> List[Dict]:
        """计算大运"""
        # 年干阴阳
        year_gan, _ = cls.get_year_gan_zhi(year)
        year_yin_yang = GAN_YIN_YANG[year_gan]
        
        # 顺逆：阳男阴女顺，阴男阳女逆
        if (year_yin_yang == '阳' and gender == '男') or (year_yin_yang == '阴' and gender == '女'):
            shun_ni = '顺'
            direction = 1
        else:
            shun_ni = '逆'
            direction = -1
        
        # 月柱为起点
        month_gan, month_zhi = cls.get_month_gan_zhi(year, month, day)
        month_gan_index = TIAN_GAN.index(month_gan)
        month_zhi_index = DI_ZHI.index(month_zhi)
        
        da_yun = []
        for i in range(8):  # 8 步大运
            gan_index = (month_gan_index + (i + 1) * direction) % 10
            zhi_index = (month_zhi_index + (i + 1) * direction) % 12
            
            da_yun.append({
                '步数': i + 1,
                '干支': TIAN_GAN[gan_index] + DI_ZHI[zhi_index],
                '天干': TIAN_GAN[gan_index],
                '地支': DI_ZHI[zhi_index],
                '起始年龄': (i + 1) * 10 + 3,  # 简化：3 岁起运
            })
        
        return da_yun
    
    @classmethod
    def get_ji_chu_duan_yu(cls, day_gan: str, si_zhu: Dict) -> List[str]:
        """生成基础断语"""
        duan_yu = []
        
        # 日干断语
        ri_gan_duan_yu = {
            '甲': '甲木参天，正直仁慈，有上进心',
            '乙': '乙木柔顺，温和善良，适应力强',
            '丙': '丙火太阳，热情开朗，表现欲强',
            '丁': '丁火灯烛，温和内敛，心思细腻',
            '戊': '戊土大地，厚重诚实，包容力强',
            '己': '己土田园，细腻谨慎，善于谋划',
            '庚': '庚金刀剑，刚毅果断，执行力强',
            '辛': '辛金珠玉，温润秀气，重面子',
            '壬': '壬水江河，聪明灵活，适应力强',
            '癸': '癸水雨露，温柔内敛，直觉敏锐',
        }
        
        if day_gan in ri_gan_duan_yu:
            duan_yu.append(f"【日主】{ri_gan_duan_yu[day_gan]}")
        
        # 五行统计
        wuxing_count = {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0}
        for zhu in ['年柱', '月柱', '日柱', '时柱']:
            gan = si_zhu[zhu][0]
            zhi = si_zhu[zhu][1]
            wuxing_count[GAN_WUXING[gan]] += 1
            wuxing_count[ZHI_WUXING[zhi]] += 1
        
        # 五行旺衰
        max_wuxing = max(wuxing_count, key=wuxing_count.get)
        min_wuxing = min(wuxing_count, key=wuxing_count.get)
        
        duan_yu.append(f"【五行】{max_wuxing}最旺（{wuxing_count[max_wuxing]}个），{min_wuxing}最弱（{wuxing_count[min_wuxing]}个）")
        
        if wuxing_count[min_wuxing] == 0:
            duan_yu.append(f"【注意】五行缺{min_wuxing}，需后天补救")
        
        return duan_yu


def bazi_pan(
    date_str: str,
    hour: int,
    gender: str = '男'
) -> Dict:
    """
    八字排盘主函数 v1.0.0
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    year, month, day = dt.year, dt.month, dt.day
    
    # 四柱
    year_gan, year_zhi = BaZiPan.get_year_gan_zhi(year)
    month_gan, month_zhi = BaZiPan.get_month_gan_zhi(year, month, day)
    day_gan, day_zhi = BaZiPan.get_day_gan_zhi(year, month, day)
    hour_gan, hour_zhi = BaZiPan.get_hour_gan_zhi(day_gan, hour)
    
    si_zhu = {
        '年柱': (year_gan, year_zhi),
        '月柱': (month_gan, month_zhi),
        '日柱': (day_gan, day_zhi),
        '时柱': (hour_gan, hour_zhi),
    }
    
    # 十神
    shi_shen = {
        '年柱': BaZiPan.get_shi_shen(day_gan, year_gan),
        '月柱': BaZiPan.get_shi_shen(day_gan, month_gan),
        '日柱': '日主',
        '时柱': BaZiPan.get_shi_shen(day_gan, hour_gan),
    }
    
    # 大运
    da_yun = BaZiPan.get_da_yun(year, month, day, hour, gender)
    
    # 基础断语
    duan_yu = BaZiPan.get_ji_chu_duan_yu(day_gan, si_zhu)
    
    # 五行统计
    wuxing_count = {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0}
    for zhu in si_zhu.values():
        wuxing_count[GAN_WUXING[zhu[0]]] += 1
        wuxing_count[ZHI_WUXING[zhu[1]]] += 1
    
    result = {
        '出生时间': f"{date_str} {hour:02d}:00",
        '性别': gender,
        '四柱': {k: f"{v[0]}{v[1]}" for k, v in si_zhu.items()},
        '十神': shi_shen,
        '五行统计': wuxing_count,
        '大运': da_yun,
        '日主': day_gan,
        '基础断语': duan_yu,
    }
    
    return result


def format_output(result: Dict) -> str:
    """格式化输出 v1.0.0"""
    output = []
    
    output.append("【八字排盘】v1.0.0")
    output.append(f"• 出生时间：{result['出生时间']}")
    output.append(f"• 性别：{result['性别']}")
    output.append("")
    output.append("【四柱】")
    output.append(f"    年柱    月柱    日柱    时柱")
    output.append(f"    {result['四柱']['年柱']}    {result['四柱']['月柱']}    {result['四柱']['日柱']}    {result['四柱']['时柱']}")
    output.append("")
    output.append("【十神】")
    output.append(f"    {result['十神']['年柱']}    {result['十神']['月柱']}    {result['十神']['日柱']}    {result['十神']['时柱']}")
    output.append("")
    output.append("【五行统计】")
    wuxing = result['五行统计']
    output.append(f"    木：{wuxing['木']}  火：{wuxing['火']}  土：{wuxing['土']}  金：{wuxing['金']}  水：{wuxing['水']}")
    
    # 检查缺五行
    que_shi = [k for k, v in wuxing.items() if v == 0]
    if que_shi:
        output.append(f"    ⚠️  五行缺：{', '.join(que_shi)}")
    
    output.append("")
    output.append("【大运】")
    for dy in result['大运']:
        output.append(f"    {dy['起始年龄']}岁：{dy['干支']}")
    
    output.append("")
    output.append("【基础断语】")
    for duan in result['基础断语']:
        output.append(f"• {duan}")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description='八字排盘工具 v1.0.0')
    parser.add_argument('--date', '-d', type=str, required=True, help='出生日期 (YYYY-MM-DD)')
    parser.add_argument('--hour', '-H', type=int, required=True, help='出生时辰 (0-23)')
    parser.add_argument('--gender', '-g', type=str, default='男', choices=['男', '女'], help='性别')
    parser.add_argument('--json', '-j', action='store_true', help='输出 JSON 格式')
    
    args = parser.parse_args()
    
    try:
        result = bazi_pan(args.date, args.hour, args.gender)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_output(result))
            
    except Exception as e:
        print(f"排盘错误：{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
