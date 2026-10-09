-- Data-only serialization: never execute save contents as Lua source.
RT_Serialize = {};
local S = RT_Serialize;
function S.Encode(value)
    local kind = type(value);
    if kind == "number" then return "n" .. tostring(value) .. ";"; end
    if kind == "boolean" then return value and "b1" or "b0"; end
    if kind == "string" then return "s" .. #value .. ":" .. value; end
    assert(kind == "table", "Unsupported saved value");
    local keys = {}; for key in pairs(value) do keys[#keys + 1] = key; end
    table.sort(keys, function(a, b) return type(a) .. tostring(a) < type(b) .. tostring(b); end);
    local out = { "t" .. #keys .. ":" };
    for _, key in ipairs(keys) do out[#out + 1] = S.Encode(key); out[#out + 1] = S.Encode(value[key]); end
    return table.concat(out);
end
function S.Decode(text)
    local position = 1;
    local function read(depth)
        assert(depth < 20, "Invalid save nesting");
        local kind = string.sub(text, position, position); position = position + 1;
        if kind == "b" then local b = string.sub(text, position, position); position = position + 1;
            assert(b == "0" or b == "1", "Invalid boolean"); return b == "1"; end
        local ending = assert(string.find(text, kind == "n" and ";" or ":", position, true));
        local n = assert(tonumber(string.sub(text, position, ending - 1))); position = ending + 1;
        if kind == "n" then return n; end
        assert(n >= 0 and n == math.floor(n) and n <= 1000000, "Invalid save length");
        if kind == "s" then
            assert(position + n - 1 <= #text, "Truncated save string");
            local result = string.sub(text, position, position + n - 1); position = position + n; return result;
        end
        assert(kind == "t", "Invalid save type");
        local result = {};
        for _ = 1, n do local key = read(depth + 1); assert(type(key) == "string" or type(key) == "number"); result[key] = read(depth + 1); end
        return result;
    end
    local result = read(0); assert(position == #text + 1, "Trailing save data"); return result;
end
