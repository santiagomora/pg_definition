#ifndef CORE_PG_BINDINGS_EXECUTION_FUNCTORS
#define CORE_PG_BINDINGS_EXECUTION_FUNCTORS
#include <stdexcept>
#include <type_traits>
#include <iostream>
#include <pqxx/pqxx>
#include "core_pg_bindings/execution/environment.hpp"


namespace core_pg_bindings
{

template<typename TP, template <typename> class CT = std::vector>
class ContainedResult_
{
public:
    using Container = CT<TP>;
    using Wrapped = TP;
};


template<typename TP>
class SingleResult_
{
public:
    using Container = TP;
    using Wrapped = TP;
};


class NoResult_
{
public:
    using Container = std::optional<bool>;
    using Wrapped = bool;
};


template<typename TP>
class OptionalResult_
{
public:
    using Container = std::optional<typename TP::Container>;
    using TPContainer = typename TP::Container;
    using Wrapped = typename TP::Wrapped;
};


template <typename, typename = std::void_t<>>
struct HasTPContainerAlias : std::false_type {};


template <typename T>
struct HasTPContainerAlias<T, std::void_t<typename T::TPContainer>> : std::true_type {};


template<typename T, typename... Args>
class base_functor
{
public:
    virtual T operator() (
        pqxx::work& tx, const std::string_view query, const std::tuple<Args...>& args
    ) const = 0;
};


template<typename T, typename... Args>
class fetch_one_functor
    : public base_functor<typename T::Container, Args...>
{
public:
    typename T::Container operator() (
        pqxx::work& tx, const std::string_view query, const std::tuple<Args...>& args
    ) const override 
    {
        if constexpr (HasTPContainerAlias<T>::value)
        {
            std::optional<std::tuple<typename T::TPContainer>> result = std::apply(
                [&tx, &query](Args&... unpacked)
                {
                    return tx.query01<typename T::TPContainer>(query.data(), {unpacked...});
                }, args);
            if (result.has_value())
            {
                return std::get<0>(result.value());
            }
            return std::nullopt;
        }
        else
        {
            std::optional<std::tuple<typename T::Container>> result = std::apply(
                [&tx, &query](Args&... unpacked)
                {
                    return tx.query01<typename T::Container>(query.data(), {unpacked...});
                }, args);
            if (!result.has_value())
            {
                throw std::invalid_argument("Could not find required result for given arguments");
            }
            return std::get<0>(result.value());
        }
    }
};


template<typename T, typename... Args>
class fetch_many_functor
    : public base_functor<typename T::Container, Args...>
{
public:
    typename T::Container operator() (
        pqxx::work& tx, const std::string_view query, const std::tuple<Args...>& args
    ) const override
    {
        if constexpr (HasTPContainerAlias<T>::value)
        {
            typename T::Container result;
            for (auto [p] : std::apply(
                [&tx, &query](Args&... unpacked) 
                {
                    return tx.query<typename T::Wrapped>(query, {unpacked...});
                }, args)
            )
            {
                if (!result.has_value())
                {
                    result = {p};
                }
                else
                {
                    result->emplace_back(p);
                }
            }
            if (result)
            {
                return *result;
            }
            return std::nullopt;
        }
        else
        {
            typename T::Container result = {};
            for (auto [p] : std::apply(
                [&tx, &query](Args&... unpacked)
                {
                    return tx.query<typename T::Wrapped>(query.data(), {unpacked...});
                }, args)
            )
            {
                result.emplace_back(p);
            }
            return result;
        }
    }
};


template<typename T, typename... Args>
class fetch_none_functor
    : public base_functor<typename T::Container, Args...>
{
public:
    typename T::Container operator() (
        pqxx::work& tx, const std::string_view query, const std::tuple<Args...>& args
    ) const override 
    {
        static_assert(std::is_same_v<T, NoResult_>, "fetch_none_functor result type must be NoResult_");
        std::apply(
            [&tx, &query](Args&... unpacked)
            {
                return tx.query01<typename T::Wrapped>(query.data(), {unpacked...});
            }, args
        );
        return std::nullopt;
    }
};

}


#endif
