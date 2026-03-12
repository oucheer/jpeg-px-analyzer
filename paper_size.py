# -*- coding: utf-8 -*-
"""
纸型配置模块
支持所有标准纸型
"""

class PaperSize:
    """纸型类"""
    
    # 标准纸型定义 (宽度, 高度) in mm
    SIZES = {
        # ISO A 系列
        'A0': (841, 1189),
        'A1': (594, 841),
        'A2': (420, 594),
        'A3': (297, 420),
        'A4': (210, 297),
        'A5': (148, 210),
        'A6': (105, 148),
        'A7': (74, 105),
        
        # ISO B 系列
        'B0': (1000, 1414),
        'B1': (707, 1000),
        'B2': (500, 707),
        'B3': (353, 500),
        'B4': (250, 353),
        'B5': (176, 250),
        'B6': (125, 176),
        
        # ANSI/Letter 系列 (美国)
        'Letter': (215.9, 279.4),
        'Legal': (215.9, 355.6),
        'Tabloid': (279.4, 431.8),
        'Executive': (184.15, 266.7),
        
        # 其他常用纸型
        'Legal 8.5x13': (215.9, 330.2),
        'Folio': (210, 330),
        'Quarto': (229, 279),
        
        # JIS 系列 (日本)
        'JIS B0': (1030, 1456),
        'JIS B1': (728, 1030),
        'JIS B2': (515, 728),
        'JIS B3': (364, 515),
        'JIS B4': (257, 364),
        'JIS B5': (182, 257),
        
        # 明信片
        'Postcard (4x6)': (101.6, 152.4),
        'Postcard (148x100)': (100, 148),
        
        # 名片
        'Business Card (90x54)': (90, 54),
        'Business Card (85x55)': (85, 55),
    }
    
    @classmethod
    def get_size(cls, name):
        """获取纸型尺寸
        
        Args:
            name: 纸型名称
            
        Returns:
            tuple: (宽度, 高度) in mm, 或 None
        """
        if name in cls.SIZES:
            return cls.SIZES[name]
        return cls.SIZES.get(name.upper())
    
    @classmethod
    def get_all_names(cls):
        """获取所有纸型名称
        
        Returns:
            list: 纸型名称列表
        """
        return sorted(cls.SIZES.keys())
    
    @classmethod
    def get_by_category(cls):
        """按类别获取纸型
        
        Returns:
            dict: 分类纸型
        """
        categories = {
            'ISO A系列': ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7'],
            'ISO B系列': ['B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6'],
            'ANSI系列': ['Letter', 'Legal', 'Tabloid', 'Executive'],
            '其他常用': ['Legal 8.5x13', 'Folio', 'Quarto'],
            'JIS系列': ['JIS B0', 'JIS B1', 'JIS B2', 'JIS B3', 'JIS B4', 'JIS B5'],
            '明信片': ['Postcard (4x6)', 'Postcard (148x100)'],
            '名片': ['Business Card (90x54)', 'Business Card (85x55)'],
        }
        return categories
    
    @classmethod
    def get_dimensions_mm(cls, name):
        """获取纸型尺寸 (mm)
        
        Args:
            name: 纸型名称
            
        Returns:
            str: 格式化的尺寸字符串
        """
        size = cls.get_size(name)
        if size:
            return f"{size[0]} x {size[1]} mm"
        return None
    
    @classmethod
    def get_dimensions_inch(cls, name):
        """获取纸型尺寸 (英寸)
        
        Args:
            name: 纸型名称
            
        Returns:
            str: 格式化的尺寸字符串
        """
        size = cls.get_size(name)
        if size:
            w_inch = size[0] / 25.4
            h_inch = size[1] / 25.4
            return f"{w_inch:.2f} x {h_inch:.2f} in"
        return None
    
    @classmethod
    def get_pixels_at_dpi(cls, name, dpi):
        """获取纸型在指定 DPI 下的像素尺寸
        
        Args:
            name: 纸型名称
            dpi: DPI 值
            
        Returns:
            tuple: (宽度, 高度) in pixels
        """
        size = cls.get_size(name)
        if size:
            w_px = int(size[0] * dpi / 25.4)
            h_px = int(size[1] * dpi / 25.4)
            return (w_px, h_px)
        return None
    
    @classmethod
    def find_by_dimensions(cls, width_mm, height_mm, tolerance=5):
        """根据尺寸查找纸型
        
        Args:
            width_mm: 宽度 (mm)
            height_mm: 高度 (mm)
            tolerance: 容差 (mm)
            
        Returns:
            str: 匹配的纸型名称，或 None
        """
        for name, (w, h) in cls.SIZES.items():
            if abs(w - width_mm) <= tolerance and abs(h - height_mm) <= tolerance:
                return name
            # 也检查旋转方向
            if abs(w - height_mm) <= tolerance and abs(h - width_mm) <= tolerance:
                return f"{name} (横向)"
        return None


class PaperConfig:
    """纸型配置管理"""
    
    def __init__(self, paper_name='A4', dpi=600):
        """初始化
        
        Args:
            paper_name: 纸型名称
            dpi: DPI 值
        """
        self.paper_name = paper_name
        self.dpi = dpi
        
        size = PaperSize.get_size(paper_name)
        if size:
            self.width_mm, self.height_mm = size
            self.width_px, self.height_px = PaperSize.get_pixels_at_dpi(paper_name, dpi)
        else:
            raise ValueError(f"不支持的纸型: {paper_name}")
    
    def set_dpi(self, dpi):
        """设置 DPI"""
        self.dpi = dpi
        self.width_px, self.height_px = PaperSize.get_pixels_at_dpi(self.paper_name, dpi)
    
    def set_paper(self, paper_name):
        """设置纸型"""
        self.paper_name = paper_name
        size = PaperSize.get_size(paper_name)
        if size:
            self.width_mm, self.height_mm = size
            self.width_px, self.height_px = PaperSize.get_pixels_at_dpi(paper_name, self.dpi)
    
    def get_info(self):
        """获取配置信息"""
        return {
            'paper_name': self.paper_name,
            'dpi': self.dpi,
            'dimensions_mm': f"{self.width_mm} x {self.height_mm} mm",
            'dimensions_px': f"{self.width_px} x {self.height_px} px",
            'dimensions_inch': f"{self.width_mm/25.4:.2f} x {self.height_mm/25.4:.2f} in",
        }


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("支持的纸型")
    print("=" * 60)
    
    categories = PaperSize.get_by_category()
    for category, papers in categories.items():
        print(f"\n{category}:")
        for p in papers:
            size = PaperSize.get_size(p)
            px = PaperSize.get_pixels_at_dpi(p, 300)
            print(f"  {p}: {size[0]}x{size[1]}mm ({px[0]}x{px[1]}px @300DPI)")
    
    print("\n" + "=" * 60)
    print("纸型配置测试")
    print("=" * 60)
    
    config = PaperConfig('A4', 600)
    print(f"\nA4 @ 600 DPI:")
    info = config.get_info()
    for k, v in info.items():
        print(f"  {k}: {v}")
