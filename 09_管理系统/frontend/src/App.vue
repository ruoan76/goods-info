<template>
  <el-container class="layout">
    <el-header class="hd">
      <div class="brand">商品主数据管理系统</div>
      <div class="env">D1 · 静态站点联通验证</div>
    </el-header>
    <el-main>
      <el-result icon="success" title="D1 静态站点已联通" sub-title="nginx :8090 → Vue3 dist · SPA 回退正常 · API 代理将在 D11 接入">
        <template #extra>
          <el-tag type="success">Vue3 + Element Plus</el-tag>
          <el-tag type="info" style="margin-left:8px">构建产物 dist</el-tag>
          <el-tag type="warning" style="margin-left:8px">API 404 属 D1 正常态</el-tag>
        </template>
      </el-result>
      <el-row :gutter="16" style="margin-top:20px">
        <el-col :span="6"><el-card shadow="never"><div class="k"><b>432万</b><span>商品主档</span></div></el-card></el-col>
        <el-col :span="6"><el-card shadow="never"><div class="k"><b>171</b><span>类目节点</span></div></el-card></el-col>
        <el-col :span="6"><el-card shadow="never"><div class="k"><b>40</b><span>API 端点</span></div></el-card></el-col>
        <el-col :span="6"><el-card shadow="never"><div class="k"><b>5</b><span>新增业务表</span></div></el-card></el-col>
      </el-row>
    </el-main>
  </el-container>
</template>

<script setup></script>

<style>
.layout{min-height:100vh}
.hd{display:flex;align-items:center;justify-content:space-between;background:#1e3a8a;color:#fff}
.brand{font-size:18px;font-weight:700}
.env{font-size:12px;opacity:.85}
.k{display:flex;flex-direction:column;align-items:center}
.k b{font-size:24px;color:#2563eb}
.k span{font-size:12px;color:#6b7280;margin-top:4px}
</style>
