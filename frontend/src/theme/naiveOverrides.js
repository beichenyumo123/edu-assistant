/**
 * Naive UI 主题覆盖 — 动物森友会风格
 *
 * 将所有 Naive UI 设计令牌映射到 warm parchment + mint teal 色板，
 * 使 Drawer / Upload / Form 等功能组件与 animal-island-vue 组件视觉统一。
 */
export const themeOverrides = {
  common: {
    // ── 主色：薄荷绿 ──
    primaryColor: '#19c8b9',
    primaryColorHover: '#3dd4c6',
    primaryColorPressed: '#50b9ab',
    primaryColorSuppl: '#e6f9f6',

    // ── 功能色 ──
    successColor: '#6fba2c',
    successColorHover: '#85cc45',
    successColorPressed: '#5a9e1e',
    successColorSuppl: '#e8f5d5',

    warningColor: '#f5c31c',
    warningColorHover: '#f7d04a',
    warningColorPressed: '#dba90e',
    warningColorSuppl: '#fef4d0',

    errorColor: '#e05a5a',
    errorColorHover: '#e87878',
    errorColorPressed: '#c94444',
    errorColorSuppl: '#fde8e8',

    infoColor: '#19c8b9',
    infoColorHover: '#3dd4c6',
    infoColorPressed: '#50b9ab',
    infoColorSuppl: '#e6f9f6',

    // ── 文本色：暖棕系 ──
    textColorBase: '#725d42',
    textColor1: '#794f27',
    textColor2: '#9f927d',
    textColor3: '#c4b89e',

    // ── 背景色：羊皮纸 ──
    bodyColor: '#f8f8f0',
    cardColor: 'rgb(247, 243, 223)',
    baseColor: 'rgb(247, 243, 223)',
    popoverColor: 'rgb(247, 243, 223)',
    tableColor: 'rgb(247, 243, 223)',
    tableColorHover: 'rgba(248, 248, 240, 0.6)',
    tableColorStriped: 'rgba(248, 248, 240, 0.6)',
    actionColor: '#f8f8f0',

    // ── 边框 & 分割线 ──
    borderColor: '#c4b89e',
    dividerColor: '#e8e2d6',

    // ── 圆角 ──
    borderRadius: '18px',
    borderRadiusSmall: '12px',
    borderRadiusLarge: '24px',

    // ── 字体 ──
    fontFamily: "Nunito, 'Noto Sans SC', 'Zen Maru Gothic', 'HarmonyOS Sans SC', 'MiSans', -apple-system, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
    fontFamilyMono: "'Fira Code', 'Cascadia Code', 'JetBrains Mono', Consolas, monospace",
    fontSize: '14px',
    fontSizeSmall: '12px',
    fontSizeMedium: '14px',
    fontSizeLarge: '16px',
    fontSizeHuge: '18px',

    // ── 输入框 ──
    inputColor: '#f7f3df',
    inputColorDisabled: '#f0ece2',

    // ── 悬停/占位 ──
    hoverColor: 'rgba(25, 200, 185, 0.08)',
    placeholderColor: '#c4b89e',
    placeholderColorDisabled: '#d9cfba',

    // ── 关闭按钮 ──
    closeColor: '#9f927d',
    closeColorHover: '#794f27',
    closeColorPressed: '#725d42',

    // ── 高度 ──
    heightSmall: '32px',
    heightMedium: '40px',
    heightLarge: '48px',

    // ── 阴影（轻量） ──
    boxShadow1: '0 2px 4px 0 rgba(61, 52, 40, 0.06)',
    boxShadow2: '0 3px 10px 0 rgba(61, 52, 40, 0.10)',
    boxShadow3: '0 8px 24px 0 rgba(61, 52, 40, 0.14)',
  },

  // ── 按钮：胶囊形 ──
  Button: {
    borderRadiusSmall: '50px',
    borderRadiusMedium: '50px',
    borderRadiusLarge: '50px',
    colorPrimary: '#19c8b9',
    colorHoverPrimary: '#3dd4c6',
    colorPressedPrimary: '#50b9ab',
    textColorPrimary: '#725d42',
    textColorHoverPrimary: '#725d42',
    textColorPressedPrimary: '#725d42',
    textColorGhostPrimary: '#19c8b9',
    textColorGhostHoverPrimary: '#3dd4c6',
    textColorGhostPressedPrimary: '#50b9ab',
    borderPrimary: '2px solid #19c8b9',
    borderHoverPrimary: '2px solid #3dd4c6',
    borderPressedPrimary: '2px solid #50b9ab',
    colorDefault: 'rgb(247, 243, 223)',
    colorHoverDefault: 'rgba(247, 243, 223, 0.85)',
    textColorDefault: '#725d42',
    borderDefault: '2px solid #aaa69d',
    borderHoverDefault: '2px solid #827157',
    border: '2px solid #aaa69d',
    borderHover: '2px solid #827157',
    boxShadowFocusPrimary: '0 0 0 3px rgba(25, 200, 185, 0.15)',
    textColorText: '#725d42',
    textColorHoverText: '#794f27',
    textColorPressedText: '#794f27',
    colorError: '#e05a5a',
    colorHoverError: '#e87878',
    colorPressedError: '#c94444',
    textColorError: '#ffffff',
  },

  // ── 输入框：羊皮纸底 + 大圆角 ──
  Input: {
    color: '#f7f3df',
    colorFocus: '#f7f3df',
    border: '2px solid #c4b89e',
    borderHover: '2px solid #827157',
    borderFocus: '2px solid #ffcc00',
    boxShadowFocus: '0 0 0 3px rgba(255, 204, 0, 0.15)',
    textColor: '#725d42',
    placeholderColor: '#c4b89e',
    borderRadius: '24px',
    lineHeight: '1.5715',
    heightSmall: '32px',
    heightMedium: '40px',
    heightLarge: '48px',
    fontSizeSmall: '12px',
    fontSizeMedium: '14px',
    fontSizeLarge: '16px',
  },

  // ── 标签：柔和圆角 ──
  Tag: {
    borderRadius: '16px',
    colorPrimary: '#e6f9f6',
    textColorPrimary: '#19c8b9',
    colorDefault: '#f0ece2',
    textColorDefault: '#9f927d',
    colorSuccess: '#e8f5d5',
    textColorSuccess: '#5a9e1e',
    colorWarning: '#fef4d0',
    textColorWarning: '#dba90e',
    colorError: '#fde8e8',
    textColorError: '#c94444',
    colorInfo: '#e6f9f6',
    textColorInfo: '#19c8b9',
  },

  // ── 抽屉 ──
  Drawer: {
    color: '#f8f8f0',
    textColor: '#725d42',
    titleTextColor: '#794f27',
    titleFontSize: '18px',
    titleFontWeight: '700',
    borderColor: '#e8e2d6',
    headerBorderColor: '#e8e2d6',
    footerBorderColor: '#e8e2d6',
  },

  // ── 折叠面板 ──
  Collapse: {
    titleTextColor: '#794f27',
    titleTextColorDisabled: '#c4b89e',
    dividerColor: '#e8e2d6',
    arrowColor: '#19c8b9',
    arrowColorDisabled: '#c4b89e',
    contentTextColor: '#725d42',
    headerColor: 'transparent',
    color: 'transparent',
  },

  // ── 气泡确认 ──
  Popconfirm: {
    color: 'rgb(247, 243, 223)',
    textColor: '#725d42',
    iconColor: '#f5c31c',
  },

  // ── 表单 ──
  Form: {
    labelTextColor: '#794f27',
    labelFontSizeLeftSmall: '14px',
    labelFontSizeLeftMedium: '14px',
    labelFontSizeLeftLarge: '16px',
    feedbackTextColor: '#9f927d',
    feedbackTextColorError: '#e05a5a',
    feedbackTextColorWarning: '#f5c31c',
    feedbackHeightSmall: '20px',
    feedbackHeightMedium: '22px',
    feedbackHeightLarge: '24px',
  },

  // ── 列表 ──
  List: {
    color: 'rgb(247, 243, 223)',
    colorHover: 'rgba(248, 248, 240, 0.6)',
    borderColor: '#e8e2d6',
    textColor: '#725d42',
    titleTextColor: '#794f27',
  },

  // ── 卡片 ──
  Card: {
    borderRadius: '20px',
    color: 'rgb(247, 243, 223)',
    colorHover: 'rgb(247, 243, 223)',
    textColor: '#725d42',
    titleTextColor: '#794f27',
    borderColor: '#e8e2d6',
    boxShadow: 'none',
    boxShadowHover: 'none',
  },

  // ── 空状态 ──
  Empty: {
    textColor: '#9f927d',
    iconColor: '#c4b89e',
  },

  // ── 加载 ──
  Spin: {
    color: '#19c8b9',
  },

  // ── 标签页 ──
  Tabs: {
    tabTextColorActiveBar: '#19c8b9',
    tabTextColorActiveLine: '#19c8b9',
    tabTextColorHoverBar: '#3dd4c6',
    tabTextColorHoverLine: '#3dd4c6',
    barColor: '#19c8b9',
    tabColor: 'transparent',
    tabTextColor: '#9f927d',
    tabTextColorActive: '#19c8b9',
    paneTextColor: '#725d42',
    tabFontWeight: '600',
    tabFontWeightActive: '700',
    tabBorderRadius: '24px',
    barWidth: '3px',
    tabGapSmallBar: '0px',
    tabGapMediumBar: '0px',
    tabGapLargeBar: '0px',
  },

  // ── 开关 ──
  Switch: {
    railColorActive: '#86d67a',
    railColor: '#d4c9b4',
  },

  // ── 复选框 ──
  Checkbox: {
    borderRadius: '8px',
    colorChecked: '#19c8b9',
    borderChecked: '2px solid #19c8b9',
    color: '#f7f3df',
    border: '2.5px solid #c4b89e',
    checkMarkColor: '#ffffff',
    boxShadowFocus: '0 0 0 3px rgba(255, 204, 0, 0.15)',
  },

  // ── 单选框 ──
  Radio: {
    borderRadius: '14px',
    colorActive: '#19c8b9',
    boxShadowFocus: '0 0 0 3px rgba(255, 204, 0, 0.15)',
    dotColorActive: '#19c8b9',
    dotColorInactive: '#c4b89e',
  },

  // ── 消息提示（Toast） ──
  Message: {
    color: 'rgb(247, 243, 223)',
    textColorSuccess: '#5a9e1e',
    textColorError: '#c94444',
    textColorWarning: '#dba90e',
    textColorInfo: '#19c8b9',
    iconColorSuccess: '#6fba2c',
    iconColorError: '#e05a5a',
    iconColorWarning: '#f5c31c',
    iconColorInfo: '#19c8b9',
    borderColorSuccess: '#6fba2c',
    borderColorError: '#e05a5a',
    borderColorWarning: '#f5c31c',
    borderColorInfo: '#19c8b9',
  },

  // ── 对话框（Modal） ──
  Dialog: {
    color: 'rgb(247, 243, 223)',
    textColor: '#725d42',
    titleTextColor: '#794f27',
    iconColor: '#19c8b9',
    border: '2px solid #e8e2d6',
  },

  // ── 通知 ──
  Notification: {
    color: 'rgb(247, 243, 223)',
    textColor: '#725d42',
    titleTextColor: '#794f27',
    borderColor: '#e8e2d6',
  },

  // ── 进度条 ──
  Progress: {
    fillColor: '#19c8b9',
    railColor: '#e8e2d6',
    textColor: '#725d42',
  },

  // ── 滑块 ──
  Slider: {
    fillColor: '#19c8b9',
    fillColorHover: '#3dd4c6',
    railColor: '#e8e2d6',
    handleColor: '#19c8b9',
    dotColor: '#19c8b9',
    dotColorModal: '#c4b89e',
  },

  // ── 下拉选择 ──
  Select: {
    peers: {
      InternalSelection: {
        color: '#f7f3df',
        colorActive: '#f7f3df',
        border: '2px solid #c4b89e',
        borderHover: '2px solid #827157',
        borderActive: '2px solid #ffcc00',
        borderFocus: '2px solid #ffcc00',
        boxShadowFocus: '0 0 0 3px rgba(255, 204, 0, 0.15)',
        textColor: '#725d42',
        borderRadius: '24px',
      },
      InternalSelectMenu: {
        color: 'rgb(247, 243, 223)',
        optionColorActive: 'rgba(25, 200, 185, 0.08)',
        optionTextColor: '#725d42',
        optionTextColorActive: '#19c8b9',
        optionTextColorHover: '#794f27',
        optionCheckColor: '#19c8b9',
      },
    },
  },

  // ── 日期选择器 ──
  DatePicker: {
    peers: {
      Input: {
        color: '#f7f3df',
        border: '2px solid #c4b89e',
      },
    },
  },

  // ── 上传 ──
  Upload: {
    draggerColor: 'rgb(247, 243, 223)',
    draggerBorder: '2px dashed #c4b89e',
    draggerBorderHover: '2px dashed #19c8b9',
    itemColorHover: 'rgba(25, 200, 185, 0.06)',
  },

  // ── 全局滚动条 ──
  Scrollbar: {
    color: '#c4b89e',
    colorHover: '#9f927d',
    width: '8px',
    borderRadius: '4px',
  },

  // ── 头像 ──
  Avatar: {
    borderRadius: '50%',
    color: '#e6f9f6',
    textColor: '#19c8b9',
  },

  // ── BackTop ──
  BackTop: {
    color: '#19c8b9',
    colorHover: '#3dd4c6',
    textColor: '#ffffff',
    boxShadow: '0 2px 8px rgba(61, 52, 40, 0.12)',
  },

  // ── Global 加载条 ──
  LoadingBar: {
    colorLoading: '#19c8b9',
  },
}
