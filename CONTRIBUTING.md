# 团队协作规范

## 目录职责划分

| 目录 | 负责人 | 说明 |
|------|--------|------|
| `backend/` | 后端开发 | FastAPI 后端服务，Python |
| `frontend/` | 前端开发 | Vue3 + Vite 前端，TypeScript |
| `data/` | 共享 | 数据集文件（只读） |
| `algorithm/` | 算法 | 数据分析与推荐算法 |

## 核心规则

### 禁止跨域修改

- **前端**：只改 `frontend/`，不要动 `backend/` 和 `algorithm/`
- **后端**：只改 `backend/`，不要动 `frontend/` 和 `algorithm/`
- **算法**：只改 `algorithm/`，不要动 `frontend/` 和 `backend/`

这样基本不会冲突。

---

## 标准提交流程

每次提交前，必须完整执行以下 4 步：

```powershell
# 1. 拉取最新代码
git pull

# 2. 查看当前状态
git status

# 3. 添加自己负责的文件夹
git add frontend          # 前端示例
# 或
git add backend           # 后端示例

# 4. 提交并推送
git commit -m "完成xxx功能"
git push
```

### 前端示例

```powershell
git pull
git add frontend
git commit -m "完成前端首页页面"
git push
```

### 后端示例

```powershell
git pull
git add backend
git commit -m "完成用户登录接口"
git push
```

---

## 提交信息格式

提交信息使用中文，格式：`"完成[功能描述]"`

**好的示例：**
- `"完成用户登录接口"`
- `"完成前端首页页面"`
- `"修复商品列表分页bug"`
- `"添加RFM分析图表"`

**不好的示例：**
- `"update"`
- `"fix"`
- `"改了点东西"`

---

## 冲突解决

如果 `git push` 时提示：

```
rejected / fetch first
```

就按以下步骤处理：

```powershell
# 先拉取合并
git pull

# 再推送
git push
```

---

## 注意事项

1. 每次提交只添加自己的文件夹，不要 `git add .` 一次性添加所有文件
2. 提交前务必 `git pull` 获取最新代码
3. 不要提交 `node_modules/`、`__pycache__/`、`dist/` 等编译产物
4. 不要提交日志文件、临时文件
5. `.env` 文件中的敏感配置仅限团队内部使用，切勿外泄
